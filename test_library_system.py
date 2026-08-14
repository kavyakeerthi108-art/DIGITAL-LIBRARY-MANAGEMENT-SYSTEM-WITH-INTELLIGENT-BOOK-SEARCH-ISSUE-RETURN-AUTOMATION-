"""
Comprehensive Test Suite for Digital Library Management System
Tests all modules: intelligent search, fine calculation, issue-return, and analytics.
"""

import unittest
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, '/home/ubuntu/library_project')

from fine_calculator import FineCalculator
from issue_return_manager import IssueReturnManager
from intelligent_search import IntelligentSearchEngine
from analytics_service import generate_all_charts


class TestFineCalculator(unittest.TestCase):
    """Test the fine calculation engine"""
    
    def setUp(self):
        self.calculator = FineCalculator()
    
    def test_no_fine_on_time(self):
        """Test no fine when returned on or before due date"""
        result = self.calculator.calculate_fine('2025-01-15', '2025-01-14')
        self.assertEqual(result['fine_amount'], 0.0)
        self.assertFalse(result['is_overdue'])
    
    def test_no_fine_within_grace_period(self):
        """Test no fine when returned within grace period"""
        result = self.calculator.calculate_fine('2025-01-15', '2025-01-17')
        self.assertEqual(result['fine_amount'], 0.0)
        self.assertTrue(result['days_overdue'] > 0)
    
    def test_fine_beyond_grace_period(self):
        """Test fine calculation beyond grace period"""
        result = self.calculator.calculate_fine('2025-01-15', '2025-01-25')
        # 10 days overdue - 3 grace = 7 effective days * 5 = 35
        self.assertEqual(result['fine_amount'], 35.0)
        self.assertTrue(result['is_overdue'])
    
    def test_faculty_discount(self):
        """Test faculty gets 50% discount"""
        result = self.calculator.calculate_fine('2025-01-15', '2025-01-25', 'faculty')
        self.assertLess(result['fine_amount'], 35.0)
    
    def test_staff_discount(self):
        """Test staff gets 25% discount"""
        result = self.calculator.calculate_fine('2025-01-15', '2025-01-25', 'staff')
        self.assertLess(result['fine_amount'], 35.0)
    
    def test_guest_surcharge(self):
        """Test guest gets 50% surcharge"""
        result = self.calculator.calculate_fine('2025-01-15', '2025-01-25', 'guest')
        self.assertGreater(result['fine_amount'], 35.0)
    
    def test_long_overdue_tiered_fines(self):
        """Test tiered fine structure for long overdue"""
        result = self.calculator.calculate_fine('2025-01-15', '2025-03-15')
        self.assertTrue(result['fine_amount'] > 0)
        self.assertEqual(result['days_overdue'], 59)
    
    def test_simple_fine_calculation(self):
        """Test simple fine calculation method"""
        fine = self.calculator.calculate_fine_simple('2025-01-15', '2025-01-25')
        self.assertEqual(fine, 35.0)
    
    def test_fine_report_generation(self):
        """Test fine report generation for multiple transactions"""
        transactions = [
            {'due_date': '2025-01-15', 'return_date': '2025-01-25'},
            {'due_date': '2025-01-15', 'return_date': '2025-01-14'},
            {'due_date': '2025-01-15', 'return_date': '2025-02-01'}
        ]
        report = self.calculator.generate_fine_report(transactions)
        self.assertGreater(report['total_fine'], 0)
        self.assertEqual(report['total_transactions'], 3)
    
    def test_max_fine_cap(self):
        """Test that fine does not exceed maximum cap"""
        result = self.calculator.calculate_fine('2025-01-01', '2025-06-01')
        self.assertLessEqual(result['fine_amount'], self.calculator.max_fine_per_book)
    
    def test_date_string_input(self):
        """Test handling of date string inputs"""
        result = self.calculator.calculate_fine('2025-01-15', '2025-01-25')
        self.assertEqual(result['fine_amount'], 35.0)


class TestIssueReturnManager(unittest.TestCase):
    """Test the issue-return automation module"""
    
    def setUp(self):
        self.manager = IssueReturnManager(loan_period=14, max_books_per_member=5)
    
    def test_successful_issue(self):
        """Test successful book issue"""
        result = self.manager.issue_book(1, 'Python Programming', 'MEM001', 'Rahul')
        self.assertTrue(result['success'])
        self.assertEqual(result['transaction']['status'], 'issued')
    
    def test_issue_unavailable_book(self):
        """Test issuing a book with no available copies"""
        self.manager.issue_book(1, 'Test Book', 'MEM001', 'Rahul')
        self.manager.issue_book(1, 'Test Book', 'MEM002', 'Priya')
        # Third issue should fail (only 1 copy)
        result = self.manager.issue_book(1, 'Test Book', 'MEM003', 'Amit')
        self.assertFalse(result['success'])
    
    def test_member_max_books_limit(self):
        """Test member cannot exceed maximum books"""
        for i in range(5):
            self.manager.issue_book(i+1, f'Book {i+1}', 'MEM001', 'Rahul')
        result = self.manager.issue_book(6, 'Book 6', 'MEM001', 'Rahul')
        self.assertFalse(result['success'])
    
    def test_successful_return(self):
        """Test successful book return"""
        self.manager.issue_book(1, 'Python', 'MEM001', 'Rahul')
        result = self.manager.return_book(1)
        self.assertTrue(result['success'])
        self.assertEqual(result['transaction']['status'], 'returned')
    
    def test_on_time_return_no_fine(self):
        """Test on-time return has no fine"""
        issue_date = datetime(2025, 1, 1).date()
        self.manager.issue_book(1, 'Python', 'MEM001', 'Rahul', 
                               loan_days=14, issue_date=issue_date)
        return_date = issue_date + timedelta(days=10)
        result = self.manager.return_book(1, return_date)
        self.assertEqual(result['fine_amount'], 0.0)
    
    def test_overdue_return_with_fine(self):
        """Test overdue return generates fine"""
        issue_date = datetime(2025, 1, 1).date()
        self.manager.issue_book(1, 'Python', 'MEM001', 'Rahul',
                               loan_days=14, issue_date=issue_date)
        return_date = issue_date + timedelta(days=25)  # 11 days overdue
        result = self.manager.return_book(1, return_date)
        self.assertGreater(result['fine_amount'], 0)
    
    def test_overdue_detection(self):
        """Test overdue book detection"""
        issue_date = datetime(2025, 1, 1).date()
        self.manager.issue_book(1, 'Python', 'MEM001', 'Rahul',
                               loan_days=14, issue_date=issue_date)
        overdue = self.manager.check_overdue_books(datetime(2025, 2, 1).date())
        self.assertGreater(len(overdue), 0)
    
    def test_member_history(self):
        """Test member borrowing history retrieval"""
        self.manager.issue_book(1, 'Book 1', 'MEM001', 'Rahul')
        self.manager.issue_book(2, 'Book 2', 'MEM001', 'Rahul')
        self.manager.return_book(1)
        history = self.manager.get_member_history('MEM001')
        self.assertEqual(history['total_transactions'], 2)
        self.assertEqual(history['returned'], 1)
        self.assertEqual(history['currently_issued'], 1)
    
    def test_library_statistics(self):
        """Test library statistics generation"""
        self.manager.issue_book(1, 'Book 1', 'MEM001', 'Rahul')
        self.manager.issue_book(2, 'Book 2', 'MEM002', 'Priya')
        self.manager.return_book(1)
        stats = self.manager.get_library_statistics()
        self.assertEqual(stats['total_transactions'], 2)
        self.assertEqual(stats['returned'], 1)
        self.assertEqual(stats['currently_issued'], 1)


class TestIntelligentSearch(unittest.TestCase):
    """Test the intelligent search engine"""
    
    def setUp(self):
        self.engine = IntelligentSearchEngine()
        self.books = [
            {
                'title': 'Python Programming', 'author': 'John Smith',
                'isbn': '978-0-123456-01-0', 'category': 'Computer Science',
                'publisher': 'Tech Publications', 'publication_year': 2023,
                'keywords': 'python programming coding computer science'
            },
            {
                'title': 'Data Structures and Algorithms', 'author': 'Jane Doe',
                'isbn': '978-0-123456-02-0', 'category': 'Computer Science',
                'publisher': 'Academic Press', 'publication_year': 2022,
                'keywords': 'data structures algorithms computer science'
            },
            {
                'title': 'Machine Learning Basics', 'author': 'Robert Chen',
                'isbn': '978-0-123456-03-0', 'category': 'Computer Science',
                'publisher': 'ML Publishing', 'publication_year': 2024,
                'keywords': 'machine learning AI data science neural networks'
            },
            {
                'title': 'Database Management Systems', 'author': 'Maria Garcia',
                'isbn': '978-0-123456-04-0', 'category': 'Computer Science',
                'publisher': 'DB Press', 'publication_year': 2021,
                'keywords': 'database SQL management systems relational'
            },
            {
                'title': 'Digital Signal Processing', 'author': 'Sarah Johnson',
                'isbn': '978-0-234567-01-0', 'category': 'Electronics',
                'publisher': 'Signal Books', 'publication_year': 2023,
                'keywords': 'signal processing digital electronics DSP'
            },
            {
                'title': 'Organic Chemistry', 'author': 'Lisa Wang',
                'isbn': '978-0-345678-01-0', 'category': 'Chemistry',
                'publisher': 'Chem Publications', 'publication_year': 2023,
                'keywords': 'organic chemistry compounds reactions'
            },
            {
                'title': 'Physics for Engineers', 'author': 'Kevin White',
                'isbn': '978-0-456789-01-0', 'category': 'Physics',
                'publisher': 'Engineering Physics', 'publication_year': 2023,
                'keywords': 'physics engineering mechanics thermodynamics'
            },
            {
                'title': 'Advanced Mathematics', 'author': 'Nancy Taylor',
                'isbn': '978-0-567890-01-0', 'category': 'Mathematics',
                'publisher': 'Math Press', 'publication_year': 2022,
                'keywords': 'mathematics calculus algebra statistics'
            },
            {
                'title': 'English Literature', 'author': 'William Clark',
                'isbn': '978-0-678901-01-0', 'category': 'Literature',
                'publisher': 'Lit Publications', 'publication_year': 2021,
                'keywords': 'literature english writing prose poetry'
            },
            {
                'title': 'Introduction to Psychology', 'author': 'Amanda Martinez',
                'isbn': '978-0-789012-01-0', 'category': 'Psychology',
                'publisher': 'Psych Books', 'publication_year': 2023,
                'keywords': 'psychology behavior cognitive science'
            }
        ]
        self.engine.build_index(self.books)
    
    def test_exact_title_search(self):
        """Test search with exact title match"""
        results = self.engine.search('Python Programming', top_k=3)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]['book']['title'], 'Python Programming')
    
    def test_author_search(self):
        """Test search by author name"""
        results = self.engine.search('Jane Doe', top_k=3)
        self.assertGreater(len(results), 0)
        self.assertTrue(any('Data Structures' in r['book']['title'] for r in results))
    
    def test_keyword_search(self):
        """Test search by keywords"""
        results = self.engine.search('machine learning AI', top_k=3)
        self.assertGreater(len(results), 0)
    
    def test_category_search(self):
        """Test search by category"""
        results = self.engine.search('Electronics', top_k=3)
        self.assertGreater(len(results), 0)
        self.assertTrue(all(r['book']['category'] == 'Electronics' for r in results))
    
    def test_no_results(self):
        """Test search with no matching results"""
        results = self.engine.search('xyznonexistent123', top_k=3)
        self.assertEqual(len(results), 0)
    
    def test_results_sorted_by_relevance(self):
        """Test that results are sorted by relevance score"""
        results = self.engine.search('computer science', top_k=5)
        for i in range(len(results) - 1):
            self.assertGreaterEqual(
                results[i]['score'], results[i+1]['score']
            )
    
    def test_book_suggestions(self):
        """Test autocomplete suggestions"""
        suggestions = self.engine.suggest_books('Python', max_suggestions=3)
        self.assertGreater(len(suggestions), 0)
        self.assertTrue(any('Python' in s['title'] for s in suggestions))
    
    def test_search_statistics(self):
        """Test search index statistics"""
        stats = self.engine.get_search_statistics()
        self.assertEqual(stats['total_books'], 10)
        self.assertGreater(stats['vocabulary_size'], 0)
    
    def test_multi_word_search(self):
        """Test search with multiple words"""
        results = self.engine.search('signal processing digital', top_k=3)
        self.assertGreater(len(results), 0)
        self.assertTrue(any('Signal' in r['book']['title'] for r in results))
    
    def test_partial_match(self):
        """Test partial word matching"""
        results = self.engine.search('Python', top_k=3)
        self.assertGreater(len(results), 0)
        self.assertTrue(any('Python' in r['book']['title'] for r in results))


class TestAnalyticsService(unittest.TestCase):
    """Test the analytics service chart generation"""
    
    def test_all_charts_generated(self):
        """Test that all analytical charts are generated successfully"""
        # This will generate all 7 charts
        generate_all_charts()
        
        # Verify all charts exist
        report_dir = '/home/ubuntu/library_project/reports'
        expected_charts = [
            'category_distribution.png',
            'transaction_summary.png',
            'fine_analysis.png',
            'availability_tracking.png',
            'monthly_trends.png',
            'member_activity.png',
            'fine_tier_analysis.png'
        ]
        
        for chart in expected_charts:
            path = os.path.join(report_dir, chart)
            self.assertTrue(os.path.exists(path), f"Chart not found: {chart}")
            self.assertGreater(os.path.getsize(path), 1000, f"Chart too small: {chart}")


class TestIntegration(unittest.TestCase):
    """End-to-end integration tests"""
    
    def test_full_workflow(self):
        """Test complete workflow: search -> issue -> return -> fine"""
        # 1. Search for a book
        engine = IntelligentSearchEngine()
        books = [
            {'title': 'Python Programming', 'author': 'John Smith',
             'isbn': '978-001', 'category': 'Computer Science',
             'publisher': 'Tech', 'publication_year': 2023,
             'keywords': 'python programming coding'},
            {'title': 'Database Systems', 'author': 'Maria Garcia',
             'isbn': '978-002', 'category': 'Computer Science',
             'publisher': 'DB Press', 'publication_year': 2021,
             'keywords': 'database SQL management'},
        ]
        engine.build_index(books)
        results = engine.search('Python')
        self.assertGreater(len(results), 0)
        
        # 2. Issue the book
        manager = IssueReturnManager()
        result = manager.issue_book(1, 'Python Programming', 'MEM001', 'Rahul')
        self.assertTrue(result['success'])
        transaction_id = result['transaction']['id']
        
        # 3. Return overdue and check fine
        issue_date = datetime(2025, 1, 1).date()
        manager.transactions[0]['issue_date'] = issue_date
        manager.transactions[0]['due_date'] = issue_date + timedelta(days=14)
        
        return_date = issue_date + timedelta(days=25)
        return_result = manager.return_book(transaction_id, return_date)
        self.assertTrue(return_result['success'])
        self.assertGreater(return_result['fine_amount'], 0)
        
        # 4. Verify fine calculation matches
        calculator = FineCalculator()
        expected_fine = calculator.calculate_fine_simple(
            manager.transactions[0]['due_date'], return_date
        )
        self.assertEqual(return_result['fine_amount'], expected_fine)
    
    def test_search_and_issue_workflow(self):
        """Test search then issue workflow"""
        engine = IntelligentSearchEngine()
        books = [
            {'title': 'Web Development', 'author': 'David Wilson',
             'isbn': '978-005', 'category': 'Computer Science',
             'publisher': 'Web Tech', 'publication_year': 2023,
             'keywords': 'web development flask python'},
            {'title': 'Database Systems', 'author': 'Maria Garcia',
             'isbn': '978-006', 'category': 'Computer Science',
             'publisher': 'DB Press', 'publication_year': 2021,
             'keywords': 'database SQL management systems'},
            {'title': 'Python Programming', 'author': 'John Smith',
             'isbn': '978-007', 'category': 'Computer Science',
             'publisher': 'Tech Publications', 'publication_year': 2023,
             'keywords': 'python programming coding'}
        ]
        engine.build_index(books)
        results = engine.search('web development', top_k=1)
        self.assertEqual(len(results), 1)
        
        manager = IssueReturnManager()
        result = manager.issue_book(1, results[0]['book']['title'], 
                                   'MEM001', 'Student')
        self.assertTrue(result['success'])
    
    def test_fine_report_integration(self):
        """Test fine report with real transaction data"""
        manager = IssueReturnManager(loan_period=14)
        
        # Issue and return several books with varying overdue days
        issue_date = datetime(2025, 1, 1).date()
        manager.issue_book(1, 'Book 1', 'MEM001', 'Rahul',
                          loan_days=14, issue_date=issue_date)
        manager.issue_book(2, 'Book 2', 'MEM002', 'Priya',
                          loan_days=14, issue_date=issue_date)
        
        # Return one on time, one late
        manager.return_book(1, issue_date + timedelta(days=10))  # On time
        manager.return_book(2, issue_date + timedelta(days=25))  # Late
        
        stats = manager.get_library_statistics()
        self.assertEqual(stats['returned'], 2)
        self.assertGreater(stats['total_fines_collected'], 0)


if __name__ == '__main__':
    # Run all tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestFineCalculator))
    suite.addTests(loader.loadTestsFromTestCase(TestIssueReturnManager))
    suite.addTests(loader.loadTestsFromTestCase(TestIntelligentSearch))
    suite.addTests(loader.loadTestsFromTestCase(TestAnalyticsService))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n{'='*60}")
    print(f"TEST RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Status: {'ALL PASSED' if result.wasSuccessful() else 'SOME FAILED'}")
