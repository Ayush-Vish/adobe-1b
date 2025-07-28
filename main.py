import json
import time
import logging
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from threading import Lock
import psutil
import gc

from pdf_parser import get_sections_from_pdf
from semanticAnalyzer import SemanticAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Results from processing a single collection."""
    collection_id: str
    success: bool
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    sections_extracted: int = 0
    processing_time: float = 0.0
    documents_processed: int = 0

class RobustPDFProcessor:
    """Thread-safe PDF processor with resource management."""
    
    def __init__(self, max_workers: Optional[int] = None):
        # Determine optimal number of workers
        cpu_count = psutil.cpu_count(logical=False)  # Physical cores
        available_memory_gb = psutil.virtual_memory().available / (1024**3)
        
        if max_workers is None:
            # Conservative approach: limit by memory (assume ~2GB per worker)
            memory_based_limit = max(1, int(available_memory_gb // 2))
            self.max_workers = min(cpu_count, memory_based_limit, 4)  # Cap at 4
        else:
            self.max_workers = max_workers
            
        logger.info(f"🚀 Initialized processor with {self.max_workers} workers")
        logger.info(f"📊 System: {cpu_count} cores, {available_memory_gb:.1f}GB available RAM")
        
        # Thread-safe locks
        self._analyzer_lock = Lock()
        self._analyzer_cache = {}
        
        # Processing statistics
        self.stats = {
            'total_collections': 0,
            'successful': 0,
            'failed': 0,
            'total_sections': 0,
            'total_documents': 0,
            'start_time': 0,
            'errors': []
        }

    def get_analyzer(self, worker_id: str) -> SemanticAnalyzer:
        """Thread-safe analyzer instance management."""
        with self._analyzer_lock:
            if worker_id not in self._analyzer_cache:
                try:
                    self._analyzer_cache[worker_id] = SemanticAnalyzer()
                    logger.debug(f"Created analyzer for worker {worker_id}")
                except Exception as e:
                    logger.error(f"Failed to create analyzer for {worker_id}: {str(e)}")
                    raise
            return self._analyzer_cache[worker_id]

    def validate_collection(self, collection_dir: Path) -> Tuple[bool, Optional[Dict]]:
        """Validate collection structure and load config."""
        try:
            input_json_path = collection_dir / "challenge1b_input.json"
            pdf_dir = collection_dir / "PDFs"
            
            if not input_json_path.exists():
                return False, None
                
            if not pdf_dir.exists():
                logger.warning(f"PDFs directory not found in {collection_dir}")
                return False, None
            
            # Load and validate JSON
            with open(input_json_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Validate required fields
            required_fields = ['challenge_info', 'persona', 'job_to_be_done', 'documents']
            for field in required_fields:
                if field not in config:
                    logger.error(f"Missing required field '{field}' in {input_json_path}")
                    return False, None
            
            # Validate PDFs exist
            documents = config.get('documents', [])
            valid_pdfs = []
            for doc in documents:
                pdf_path = pdf_dir / doc['filename']
                if pdf_path.exists() and pdf_path.suffix.lower() == '.pdf':
                    valid_pdfs.append(doc['filename'])
                else:
                    logger.warning(f"PDF not found or invalid: {pdf_path}")
            
            if not valid_pdfs:
                logger.error(f"No valid PDFs found in {collection_dir}")
                return False, None
            
            # Update config with only valid PDFs
            config['valid_pdfs'] = valid_pdfs
            
            return True, config
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {collection_dir}: {str(e)}")
            return False, None
        except Exception as e:
            logger.error(f"Error validating {collection_dir}: {str(e)}")
            return False, None

    def process_single_collection(self, collection_dir: Path, output_dir: Path, worker_id: str) -> ProcessingResult:
        """Process a single collection with comprehensive error handling."""
        start_time = time.time()
        collection_id = collection_dir.name
        
        try:
            logger.info(f"🔍 [{worker_id}] Processing {collection_id}")
            
            # Validate collection
            is_valid, config = self.validate_collection(collection_dir)
            if not is_valid:
                return ProcessingResult(
                    collection_id=collection_id,
                    success=False,
                    error_message="Collection validation failed"
                )
            
            # Extract configuration
            challenge_info = config.get("challenge_info", {})
            challenge_id = challenge_info.get("challenge_id", collection_id)
            persona = config.get("persona", {}).get("role", "")
            job_to_be_done = config.get("job_to_be_done", {}).get("task", "")
            valid_pdfs = config.get("valid_pdfs", [])
            
            logger.info(f"📝 [{worker_id}] {challenge_id}: {len(valid_pdfs)} PDFs, Persona: {persona[:50]}...")
            
            # Get analyzer for this worker
            analyzer = self.get_analyzer(worker_id)
            
            # Process PDFs with individual error handling
            all_sections = []
            successful_pdfs = []
            pdf_dir = collection_dir / "PDFs"
            
            for pdf_file in valid_pdfs:
                try:
                    pdf_path = pdf_dir / pdf_file
                    sections = get_sections_from_pdf(str(pdf_path))
                    
                    if sections:
                        all_sections.extend(sections)
                        successful_pdfs.append(pdf_file)
                        logger.debug(f"✅ [{worker_id}] {pdf_file}: {len(sections)} sections")
                    else:
                        logger.warning(f"⚠️ [{worker_id}] No sections extracted from {pdf_file}")
                        
                except Exception as e:
                    logger.error(f"❌ [{worker_id}] Error processing {pdf_file}: {str(e)}")
                    continue
            
            if not all_sections:
                return ProcessingResult(
                    collection_id=collection_id,
                    success=False,
                    error_message="No sections extracted from any PDF",
                    documents_processed=len(successful_pdfs)
                )
            
            # Rank sections
            try:
                ranked_sections = analyzer.rank_sections(all_sections, persona, job_to_be_done)
                logger.debug(f"🎯 [{worker_id}] Ranked {len(ranked_sections)} sections")
            except Exception as e:
                logger.error(f"❌ [{worker_id}] Ranking failed: {str(e)}")
                return ProcessingResult(
                    collection_id=collection_id,
                    success=False,
                    error_message=f"Section ranking failed: {str(e)}",
                    sections_extracted=len(all_sections),
                    documents_processed=len(successful_pdfs)
                )
            
            # Generate output
            try:
                output = analyzer.generate_output(
                    successful_pdfs, persona, job_to_be_done, ranked_sections
                )
                output["challenge_info"] = challenge_info
            except Exception as e:
                logger.error(f"❌ [{worker_id}] Output generation failed: {str(e)}")
                return ProcessingResult(
                    collection_id=collection_id,
                    success=False,
                    error_message=f"Output generation failed: {str(e)}",
                    sections_extracted=len(all_sections),
                    documents_processed=len(successful_pdfs)
                )
            
            # Save output
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f"challenge1b_output_{challenge_id}.json"
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(output, f, indent=4, ensure_ascii=False)
                
                processing_time = time.time() - start_time
                logger.info(f"✅ [{worker_id}] {collection_id} completed in {processing_time:.2f}s")
                
                return ProcessingResult(
                    collection_id=collection_id,
                    success=True,
                    output_path=str(output_path),
                    sections_extracted=len(all_sections),
                    processing_time=processing_time,
                    documents_processed=len(successful_pdfs)
                )
                
            except Exception as e:
                logger.error(f"❌ [{worker_id}] Failed to save output: {str(e)}")
                return ProcessingResult(
                    collection_id=collection_id,
                    success=False,
                    error_message=f"Failed to save output: {str(e)}",
                    sections_extracted=len(all_sections),
                    documents_processed=len(successful_pdfs)
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ [{worker_id}] {collection_id}: {error_msg}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            return ProcessingResult(
                collection_id=collection_id,
                success=False,
                error_message=error_msg,
                processing_time=processing_time
            )
        finally:
            # Force garbage collection to free memory
            gc.collect()

    # ...existing code...
    def discover_collections(self, base_dir: Path) -> List[Path]:
        """Discover and validate collection directories."""
        logger.info(f"🔍 Discovering collections in {base_dir}")
        
        if not base_dir.exists():
            logger.error(f"Base directory does not exist: {base_dir}")
            return []
        
        collections = []
        for item in base_dir.iterdir():
            # Updated condition to handle "Collection 1", "Collection 2", etc.
            if item.is_dir() and (item.name.startswith("Collection") or item.name.lower().startswith("collection")):
                is_valid, _ = self.validate_collection(item)
                if is_valid:
                    collections.append(item)
                    logger.debug(f"✅ Found valid collection: {item.name}")
                else:
                    logger.warning(f"⚠️ Invalid collection skipped: {item.name}")
        
        logger.info(f"📊 Found {len(collections)} valid collections")
        return collections
    # ...existing code...

    def process_all_collections(self, base_dir: str, output_dir: str) -> Dict:
        """Process all collections with multi-threading and comprehensive reporting."""
        self.stats['start_time'] = time.time()
        
        base_path = Path(base_dir)
        output_path = Path(output_dir)
        
        # Discover collections
        collections = self.discover_collections(base_path)
        self.stats['total_collections'] = len(collections)
        
        if not collections:
            logger.error("No valid collections found!")
            return self._generate_final_report()
        
        logger.info(f"🚀 Starting parallel processing with {self.max_workers} workers")
        
        # Process collections in parallel
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_collection = {
                executor.submit(
                    self.process_single_collection, 
                    collection, 
                    output_path, 
                    f"worker-{i % self.max_workers}"
                ): collection 
                for i, collection in enumerate(collections)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_collection):
                collection = future_to_collection[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Update statistics
                    if result.success:
                        self.stats['successful'] += 1
                        self.stats['total_sections'] += result.sections_extracted
                        self.stats['total_documents'] += result.documents_processed
                    else:
                        self.stats['failed'] += 1
                        self.stats['errors'].append({
                            'collection': result.collection_id,
                            'error': result.error_message
                        })
                    
                    # Progress update
                    completed = len(results)
                    progress = (completed / len(collections)) * 100
                    logger.info(f"📈 Progress: {completed}/{len(collections)} ({progress:.1f}%)")
                    
                except Exception as e:
                    logger.error(f"❌ Task failed for {collection.name}: {str(e)}")
                    self.stats['failed'] += 1
                    self.stats['errors'].append({
                        'collection': collection.name,
                        'error': f"Task execution failed: {str(e)}"
                    })
        
        # Clean up analyzer cache
        with self._analyzer_lock:
            self._analyzer_cache.clear()
        
        return self._generate_final_report()

    def _generate_final_report(self) -> Dict:
        """Generate comprehensive processing report."""
        total_time = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
        
        report = {
            'summary': {
                'total_collections': self.stats['total_collections'],
                'successful': self.stats['successful'],
                'failed': self.stats['failed'],
                'success_rate': (self.stats['successful'] / max(1, self.stats['total_collections'])) * 100,
                'total_processing_time': total_time,
                'total_sections_extracted': self.stats['total_sections'],
                'total_documents_processed': self.stats['total_documents']
            },
            'performance': {
                'avg_time_per_collection': total_time / max(1, self.stats['successful']),
                'sections_per_collection': self.stats['total_sections'] / max(1, self.stats['successful']),
                'max_workers_used': self.max_workers
            },
            'errors': self.stats['errors']
        }
        
        # Log final report
        logger.info("\n" + "="*60)
        logger.info("📊 FINAL PROCESSING REPORT")
        logger.info("="*60)
        logger.info(f"📁 Total Collections: {report['summary']['total_collections']}")
        logger.info(f"✅ Successful: {report['summary']['successful']}")
        logger.info(f"❌ Failed: {report['summary']['failed']}")
        logger.info(f"🎯 Success Rate: {report['summary']['success_rate']:.1f}%")
        logger.info(f"📋 Total Sections: {report['summary']['total_sections_extracted']}")
        logger.info(f"📄 Total Documents: {report['summary']['total_documents_processed']}")
        logger.info(f"⏱️ Total Time: {total_time:.2f}s")
        logger.info(f"⚡ Avg Time/Collection: {report['performance']['avg_time_per_collection']:.2f}s")
        
        if report['errors']:
            logger.info(f"\n❌ ERRORS ({len(report['errors'])}):")
            for error in report['errors'][:5]:  # Show first 5 errors
                logger.info(f"   • {error['collection']}: {error['error']}")
            if len(report['errors']) > 5:
                logger.info(f"   ... and {len(report['errors']) - 5} more errors")
        
        logger.info("="*60)
        
        return report

def main():
    """Main execution function with argument parsing."""
    import argparse
    parser = argparse.ArgumentParser(description='Robust Multi-threaded PDF Processor')
    parser.add_argument('--base-dir', default='./',  # Current directory
                       help='Base directory containing collections')
    parser.add_argument('--output-dir', default='./output',
                       help='Output directory for results')
    parser.add_argument('--workers', type=int, default=None,
                       help='Number of worker threads (auto-detect if not specified)')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Create processor
    processor = RobustPDFProcessor(max_workers=args.workers)
    
    # Process all collections
    try:
        report = processor.process_all_collections(args.base_dir, args.output_dir)
        
        # Save report
        report_path = Path(args.output_dir) / 'processing_report.json'
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=4)
        
        logger.info(f"📊 Detailed report saved to: {report_path}")
        
        # Exit with appropriate code
        exit_code = 0 if report['summary']['failed'] == 0 else 1
        return exit_code
        
    except KeyboardInterrupt:
        logger.info("🛑 Processing interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"💥 Fatal error: {str(e)}")
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    exit(main())