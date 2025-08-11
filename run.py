"""
VedOps Pipeline Runner
Automated execution script for CI/CD integration
"""
import asyncio
import argparse
import json
import sys
import os
from pathlib import Path

from utils.orchestrator import VedOpsOrchestrator
from utils.project_manager import ProjectManager

async def run_automated_pipeline(config_path: str):
    """Run pipeline with configuration file"""
    try:
        # Load configuration
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"🚀 Starting VedOps automated pipeline...")
        print(f"📋 Configuration: {config_path}")
        
        # Initialize orchestrator
        orchestrator = VedOpsOrchestrator()
        
        # Execute pipeline
        results = await orchestrator.execute_pipeline(config)
        
        # Output results
        if results["status"] == "success":
            print("✅ Pipeline completed successfully!")
            print(f"📊 Duration: {results.get('pipeline_duration', 'Unknown')}")
            
            # Save results
            results_path = "pipeline_results.json"
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"📄 Results saved to: {results_path}")
            
            return 0
        else:
            print(f"❌ Pipeline failed: {results.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        print(f"💥 Pipeline execution failed: {str(e)}")
        return 1

def main():
    parser = argparse.ArgumentParser(description="VedOps Automated Pipeline Runner")
    parser.add_argument(
        "--config", 
        required=True, 
        help="Path to pipeline configuration JSON file"
    )
    parser.add_argument(
        "--output", 
        default="pipeline_results.json",
        help="Output file for pipeline results"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.config):
        print(f"❌ Configuration file not found: {args.config}")
        sys.exit(1)
    
    # Run pipeline
    exit_code = asyncio.run(run_automated_pipeline(args.config))
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
