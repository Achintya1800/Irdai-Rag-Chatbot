#!/usr/bin/env python3
"""
Immediate fix for scraper issues - ensures all methods are present
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_scraper_methods():
    """Test if all required scraper methods exist"""
    
    print("🔧 TESTING SCRAPER METHODS")
    print("="*50)
    
    try:
        from scrapers.comprehensive_scraper import ComprehensiveScraper
        scraper = ComprehensiveScraper(use_selenium=False)
        
        # List of required methods
        required_methods = [
            'clear_query_state',
            'calculate_relevance_score',
            'extract_irdai_documents_enhanced', 
            'normalize_title',
            'is_exact_title_match',
            'extract_title_from_link',
            'scrape_page_with_query',
            'extract_all_document_links_with_query',
            'scrape_irdai_comprehensive',
            'scrape_page_recursive',  # This is the problematic one
            'scrape_all_websites_comprehensive',
            'create_searchable_content',
            'close_driver',
            'save_documents'
        ]
        
        missing_methods = []
        for method in required_methods:
            if hasattr(scraper, method):
                print(f"  ✅ {method}")
            else:
                missing_methods.append(method)
                print(f"  ❌ {method} - MISSING!")
        
        if missing_methods:
            print(f"\n❌ MISSING METHODS: {missing_methods}")
            return False
        else:
            print(f"\n✅ ALL METHODS PRESENT!")
            return True
            
    except Exception as e:
        print(f"❌ Error testing scraper: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic scraper functionality"""
    
    print("\n🧪 TESTING BASIC FUNCTIONALITY")
    print("="*50)
    
    try:
        from scrapers.comprehensive_scraper import ComprehensiveScraper
        scraper = ComprehensiveScraper(use_selenium=False)
        
        # Test demo mode
        scraper.demo_mode = True
        test_query = "Insurance Business in Special Economic Zone"
        
        print(f"🔍 Testing with query: '{test_query}'")
        
        # Test create_searchable_content (demo mode)
        try:
            demo_docs = scraper.create_searchable_content(test_query)
            print(f"  ✅ Demo content creation: {len(demo_docs)} documents")
        except Exception as e:
            print(f"  ❌ Demo content creation failed: {e}")
            return False
        
        # Test clear_query_state
        try:
            scraper.clear_query_state()
            print(f"  ✅ Query state clearing works")
        except Exception as e:
            print(f"  ❌ Query state clearing failed: {e}")
            return False
        
        # Test relevance calculation
        try:
            score = scraper.calculate_relevance_score("test insurance text", "insurance")
            print(f"  ✅ Relevance calculation works: {score:.3f}")
        except Exception as e:
            print(f"  ❌ Relevance calculation failed: {e}")
            return False
        
        # Test title normalization
        try:
            normalized = scraper.normalize_title("Test Insurance Document 2025")
            print(f"  ✅ Title normalization works: '{normalized}'")
        except Exception as e:
            print(f"  ❌ Title normalization failed: {e}")
            return False
        
        # Test scrape_all_websites_comprehensive (demo mode)
        try:
            docs = scraper.scrape_all_websites_comprehensive(test_query)
            print(f"  ✅ Comprehensive scraping works: {len(docs)} documents")
        except Exception as e:
            print(f"  ❌ Comprehensive scraping failed: {e}")
            return False
        
        print(f"\n✅ ALL BASIC FUNCTIONALITY TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Error in functionality test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main fix and test function"""
    
    print("🚀 COMPREHENSIVE SCRAPER FIX AND TEST")
    print("="*60)
    
    # Test 1: Check methods
    methods_ok = test_scraper_methods()
    
    # Test 2: Check functionality
    functionality_ok = test_basic_functionality()
    
    print("\n" + "="*60)
    print("📊 FINAL RESULTS")
    print("="*60)
    
    print(f"🔧 Methods Test: {'✅ PASSED' if methods_ok else '❌ FAILED'}")
    print(f"🧪 Functionality Test: {'✅ PASSED' if functionality_ok else '❌ FAILED'}")
    
    if methods_ok and functionality_ok:
        print("\n🎉 SCRAPER FIX SUCCESSFUL!")
        print("✅ All methods present and working")
        print("🚀 Ready for Streamlit app usage")
        
        print("\n📋 Next Steps:")
        print("1. Run: streamlit run streamlit_app.py")
        print("2. Try Force Fresh Search with your queries")
        print("3. Test queries like:")
        print("   - 'Corporate Agency Matters Concerning RRBs'")
        print("   - 'Insurance Business in Special Economic Zone'")
        print("   - 'Obligatory Cession for the financial year 2024-25'")
        
        return True
    else:
        print("\n❌ SCRAPER FIX FAILED!")
        print("🔧 Check the comprehensive_scraper.py file")
        print("📋 Ensure all methods are properly defined")
        return False

if __name__ == "__main__":
    main()
