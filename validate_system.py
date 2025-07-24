#!/usr/bin/env python3
"""
REFACTORED: Production system validation with RRB test case
"""

import sys
import os
import re

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from rag.rag_system import RAGSystem
    from rag.vector_db import VectorDatabase
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("🔧 Make sure you're running from the project root directory")
    sys.exit(1)

def validate_production_system():
    """
    REFACTORED: Validate production system with specific test cases
    """
    
    print("🔍 PRODUCTION SYSTEM VALIDATION")
    print("="*60)
    
    try:
        # Initialize systems
        print("🔄 Initializing RAG system...")
        rag_system = RAGSystem()
        vector_db = VectorDatabase()
        
        # Check database status
        print("📊 Checking database status...")
        stats = vector_db.get_collection_stats()
        total_docs = stats.get('total_documents', 0)
        
        print(f"📊 Database Status: {total_docs} documents loaded")
        
        if total_docs == 0:
            print("❌ ERROR: No documents in database!")
            print("🔧 Run: python fix_all_websites_system.py")
            return False
        
        # NEW: Production-specific test cases
        production_test_cases = [
            {
                "query": "Corporate Agency Matters Concerning RRBs Amalgamated from 1st May 2025 and Beyond",
                "expected_doc_id": "7269046",
                "expected_keywords": ["rrb", "amalgamat", "corporate agency", "may 2025", "01.05.2025"],
                "min_confidence": 0.85,
                "description": "RRB Amalgamation Test Case"
            },
            {
                "query": "Reconstitution of Inter-Disciplinary Standing Committee on Cyber Security",
                "expected_keywords": ["reconstitution", "inter-disciplinary", "standing committee", "cyber security"],
                "min_confidence": 0.3,  # Lower threshold for this specific case
                "description": "Cyber Security Committee Test"
            },
            {
                "query": "ULIP regulations 2024",
                "expected_keywords": ["ulip", "unit linked", "regulation"],
                "min_confidence": 0.7,
                "description": "ULIP Regulation Test"
            },
            {
                "query": "Insurance Amendment Act 2021",
                "expected_keywords": ["insurance", "amendment", "act", "2021"],
                "min_confidence": 0.7,
                "description": "Amendment Act Test"
            }
        ]
        
        print(f"\n🎯 PRODUCTION TEST CASES")
        print("-" * 50)
        
        passed_tests = 0
        total_tests = len(production_test_cases)
        
        for test_case in production_test_cases:
            print(f"\n🔍 Testing: {test_case['description']}")
            print(f"Query: {test_case['query']}")
            
            try:
                response = rag_system.query(test_case['query'])
                
                # Test 1: Confidence Score
                confidence_pass = response.confidence_score >= test_case['min_confidence']
                print(f"  Confidence: {response.confidence_score:.3f} (Required: {test_case['min_confidence']}) {'✅' if confidence_pass else '❌'}")
                
                # Test 2: Keyword Presence
                answer_lower = response.answer.lower()
                keywords_found = sum(1 for keyword in test_case['expected_keywords'] if keyword in answer_lower)
                keyword_pass = keywords_found >= len(test_case['expected_keywords']) * 0.6  # 60% of keywords
                print(f"  Keywords: {keywords_found}/{len(test_case['expected_keywords'])} found {'✅' if keyword_pass else '❌'}")
                
                # Test 3: Document ID (if specified)
                doc_id_pass = True
                if 'expected_doc_id' in test_case:
                    found_doc_ids = []
                    for source in response.sources:
                        for link in source.get('document_links', []):
                            if 'documentId=' in link:
                                doc_id_match = re.search(r'documentId=(\d+)', link)
                                if doc_id_match:
                                    found_doc_ids.append(doc_id_match.group(1))
                    
                    doc_id_pass = test_case['expected_doc_id'] in found_doc_ids
                    print(f"  Document ID: Expected {test_case['expected_doc_id']}, Found {found_doc_ids} {'✅' if doc_id_pass else '❌'}")
                
                # Test 4: Sources Available
                sources_pass = len(response.sources) > 0
                print(f"  Sources: {len(response.sources)} found {'✅' if sources_pass else '❌'}")
                
                # Overall test result
                test_passed = confidence_pass and keyword_pass and doc_id_pass and sources_pass
                if test_passed:
                    passed_tests += 1
                    print(f"  🎉 TEST PASSED")
                else:
                    print(f"  ❌ TEST FAILED")
                
            except Exception as e:
                print(f"  ❌ Test error: {e}")
        
        # NEW: RRB-specific validation
        print(f"\n🎯 RRB AMALGAMATION SPECIFIC TEST")
        print("-" * 40)
        
        rrb_query = "Corporate Agency Matters Concerning RRBs Amalgamated from 1st May 2025 and Beyond"
        try:
            rrb_response = rag_system.query(rrb_query)
            
            # Check for specific RRB document
            rrb_doc_found = False
            for source in rrb_response.sources:
                title = source.get('title', '').lower()
                if 'rrb' in title and 'amalgamat' in title and '2025' in title:
                    rrb_doc_found = True
                    print(f"  ✅ RRB document found: {source.get('title', '')[:60]}...")
                    break
            
            if not rrb_doc_found:
                print(f"  ❌ Specific RRB amalgamation document not found")
            
            # Check for document ID 7269046
            target_doc_id = "7269046"
            doc_id_found = False
            for source in rrb_response.sources:
                for link in source.get('document_links', []):
                    if f'documentId={target_doc_id}' in link:
                        doc_id_found = True
                        print(f"  ✅ Target document ID {target_doc_id} found")
                        break
                if doc_id_found:
                    break
            
            if not doc_id_found:
                print(f"  ❌ Target document ID {target_doc_id} not found")
            
            rrb_test_passed = rrb_doc_found and doc_id_found
            
        except Exception as e:
            print(f"  ❌ RRB test error: {e}")
            rrb_test_passed = False
        
        # Overall assessment
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("\n" + "="*60)
        print("📊 PRODUCTION VALIDATION RESULTS")
        print("="*60)
        print(f"Standard Tests: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
        print(f"RRB Specific Test: {'✅ PASSED' if rrb_test_passed else '❌ FAILED'}")
        
        overall_success = success_rate >= 70 and rrb_test_passed
        
        if overall_success:
            print("🎉 PRODUCTION SYSTEM VALIDATION PASSED!")
            print("✅ System ready for production use!")
        else:
            print("❌ PRODUCTION SYSTEM VALIDATION FAILED!")
            print("🔧 System needs fixes before production use")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

def main():
    """REFACTORED: Production validation main"""
    
    success = validate_production_system()
    
    print("\n" + "="*60)
    if success:
        print("🎉 PRODUCTION VALIDATION PASSED!")
        print("✅ System ready for production deployment!")
        print("\n🚀 Next Steps:")
        print("1. Run: streamlit run streamlit_app.py")
        print("2. Test with: 'Corporate Agency Matters Concerning RRBs Amalgamated from 1st May 2025 and Beyond'")
        print("3. Verify document ID 7269046 appears at top of results")
    else:
        print("❌ PRODUCTION VALIDATION FAILED!")
        print("🔧 Run: python fix_all_websites_system.py")
        print("Then re-run validation")

if __name__ == "__main__":
    main()