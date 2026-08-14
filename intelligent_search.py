"""
Intelligent Book Search Module
Implements TF-IDF based semantic search, fuzzy matching, and relevance scoring
for the Digital Library Management System.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class IntelligentSearchEngine:
    """
    Advanced search engine that combines TF-IDF vectorization with
    multi-field relevance scoring for intelligent book search.
    """
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95
        )
        self.book_corpus = []
        self.book_metadata = []
        self.is_trained = False
    
    def build_index(self, books):
        """
        Build the search index from a list of book dictionaries.
        
        Args:
            books: List of dicts with keys: title, author, isbn, category,
                   publisher, keywords, publication_year
        """
        self.book_corpus = []
        self.book_metadata = []
        
        for book in books:
            # Create a composite text representation for TF-IDF
            text_parts = [
                book.get('title', ''),
                book.get('author', ''),
                book.get('category', ''),
                book.get('publisher', ''),
                book.get('keywords', ''),
                str(book.get('publication_year', ''))
            ]
            composite_text = ' '.join(text_parts)
            self.book_corpus.append(composite_text)
            self.book_metadata.append(book)
        
        # Fit the vectorizer on the corpus
        self.tfidf_matrix = self.vectorizer.fit_transform(self.book_corpus)
        self.is_trained = True
        print(f"Search index built with {len(books)} books.")
    
    def search(self, query, top_k=10, min_score=0.05):
        """
        Perform intelligent search with relevance scoring.
        
        Args:
            query: Search query string
            top_k: Maximum number of results to return
            min_score: Minimum relevance score threshold
            
        Returns:
            List of search results sorted by relevance
        """
        if not self.is_trained:
            return []
        
        # Transform query using the fitted vectorizer
        query_vector = self.vectorizer.transform([query])
        
        # Calculate cosine similarity between query and all books
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        # Apply field-specific weighting bonuses
        query_lower = query.lower().split()
        results = []
        
        for i, similarity in enumerate(similarities):
            if similarity < min_score:
                continue
            
            book = self.book_metadata[i]
            final_score = similarity
            
            # Title match bonus (highest weight)
            title_lower = book.get('title', '').lower()
            title_words = title_lower.split()
            for q_word in query_lower:
                if q_word in title_words:
                    final_score += 0.15
                elif q_word in title_lower:
                    final_score += 0.10
            
            # Author match bonus
            author_lower = book.get('author', '').lower()
            for q_word in query_lower:
                if q_word in author_lower:
                    final_score += 0.08
            
            # ISBN exact match bonus
            isbn = book.get('isbn', '')
            if query.lower() in isbn.lower():
                final_score += 0.20
            
            # Category match bonus
            category_lower = book.get('category', '').lower()
            for q_word in query_lower:
                if q_word in category_lower:
                    final_score += 0.05
            
            result = {
                'book': book,
                'score': round(final_score, 4),
                'match_fields': []
            }
            
            # Track which fields matched
            for q_word in query_lower:
                if q_word in title_lower:
                    result['match_fields'].append('title')
                if q_word in author_lower:
                    result['match_fields'].append('author')
                if q_word in category_lower:
                    result['match_fields'].append('category')
                if q_word in book.get('keywords', '').lower():
                    result['match_fields'].append('keywords')
            
            results.append(result)
        
        # Sort by final score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:top_k]
    
    def suggest_books(self, query, max_suggestions=5):
        """
        Provide book suggestions for autocomplete functionality.
        
        Args:
            query: Partial search query
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List of suggested book titles
        """
        suggestions = []
        query_lower = query.lower()
        
        for book in self.book_metadata:
            title = book.get('title', '')
            if query_lower in title.lower():
                suggestions.append({
                    'title': title,
                    'author': book.get('author', ''),
                    'category': book.get('category', ''),
                    'score': len(query_lower) / len(title)  # Simple relevance
                })
        
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        return suggestions[:max_suggestions]
    
    def get_search_statistics(self):
        """Return statistics about the search index"""
        if not self.is_trained:
            return {}
        
        # Calculate term frequency statistics
        feature_names = self.vectorizer.get_feature_names_out()
        
        return {
            'total_books': len(self.book_corpus),
            'total_terms': len(feature_names),
            'most_common_terms': sorted(
                self.tfidf_matrix.mean(axis=0).A1.tolist(),
                reverse=True
            )[:10],
            'vocabulary_size': len(feature_names)
        }


def demo_search():
    """Demonstrate the intelligent search capabilities"""
    # Sample book data
    books = [
        {
            'title': 'Python Programming', 'author': 'John Smith',
            'isbn': '978-0-123456-01-0', 'category': 'Computer Science',
            'publisher': 'Tech Publications', 'publication_year': 2023,
            'keywords': 'python programming coding computer science algorithms'
        },
        {
            'title': 'Data Structures and Algorithms', 'author': 'Jane Doe',
            'isbn': '978-0-123456-02-0', 'category': 'Computer Science',
            'publisher': 'Academic Press', 'publication_year': 2022,
            'keywords': 'data structures algorithms computer science programming'
        },
        {
            'title': 'Introduction to Machine Learning', 'author': 'Robert Chen',
            'isbn': '978-0-123456-03-0', 'category': 'Computer Science',
            'publisher': 'ML Publishing', 'publication_year': 2024,
            'keywords': 'machine learning artificial intelligence AI data science'
        },
        {
            'title': 'Database Management Systems', 'author': 'Maria Garcia',
            'isbn': '978-0-123456-04-0', 'category': 'Computer Science',
            'publisher': 'DB Press', 'publication_year': 2021,
            'keywords': 'database SQL management systems data storage'
        },
        {
            'title': 'Web Development with Flask', 'author': 'David Wilson',
            'isbn': '978-0-123456-05-0', 'category': 'Computer Science',
            'publisher': 'Web Tech Books', 'publication_year': 2023,
            'keywords': 'web development flask python backend API'
        },
        {
            'title': 'Operating Systems Concepts', 'author': 'Thomas Anderson',
            'isbn': '978-0-123456-06-0', 'category': 'Computer Science',
            'publisher': 'OS Publications', 'publication_year': 2022,
            'keywords': 'operating systems OS kernel processes threads'
        },
        {
            'title': 'Digital Signal Processing', 'author': 'Sarah Johnson',
            'isbn': '978-0-234567-01-0', 'category': 'Electronics',
            'publisher': 'Signal Books', 'publication_year': 2023,
            'keywords': 'signal processing digital electronics DSP filters'
        },
        {
            'title': 'Microprocessor Systems', 'author': 'James Brown',
            'isbn': '978-0-234567-02-0', 'category': 'Electronics',
            'publisher': 'Micro Press', 'publication_year': 2022,
            'keywords': 'microprocessor embedded systems CPU architecture'
        },
        {
            'title': 'Organic Chemistry', 'author': 'Lisa Wang',
            'isbn': '978-0-345678-01-0', 'category': 'Chemistry',
            'publisher': 'Chem Publications', 'publication_year': 2023,
            'keywords': 'organic chemistry compounds reactions synthesis'
        },
        {
            'title': 'Physics for Engineers', 'author': 'Kevin White',
            'isbn': '978-0-456789-01-0', 'category': 'Physics',
            'publisher': 'Engineering Physics', 'publication_year': 2023,
            'keywords': 'physics engineering mechanics thermodynamics optics'
        },
        {
            'title': 'Advanced Mathematics', 'author': 'Nancy Taylor',
            'isbn': '978-0-567890-01-0', 'category': 'Mathematics',
            'publisher': 'Math Press', 'publication_year': 2022,
            'keywords': 'mathematics calculus algebra statistics probability'
        },
        {
            'title': 'English Literature', 'author': 'William Clark',
            'isbn': '978-0-678901-01-0', 'category': 'Literature',
            'publisher': 'Lit Publications', 'publication_year': 2021,
            'keywords': 'literature english writing prose poetry drama'
        },
        {
            'title': 'Introduction to Psychology', 'author': 'Amanda Martinez',
            'isbn': '978-0-789012-01-0', 'category': 'Psychology',
            'publisher': 'Psych Books', 'publication_year': 2023,
            'keywords': 'psychology behavior cognitive science mental health'
        },
        {
            'title': 'Economics Fundamentals', 'author': 'Christopher Hall',
            'isbn': '978-0-890123-01-0', 'category': 'Economics',
            'publisher': 'Econ Press', 'publication_year': 2022,
            'keywords': 'economics microeconomics macroeconomics market trade'
        },
        {
            'title': 'Environmental Science', 'author': 'Jennifer Adams',
            'isbn': '978-0-901234-01-0', 'category': 'Science',
            'publisher': 'Eco Publications', 'publication_year': 2024,
            'keywords': 'environment ecology sustainability climate pollution'
        },
        {
            'title': 'Business Management', 'author': 'Richard Thompson',
            'isbn': '978-1-012345-01-0', 'category': 'Management',
            'publisher': 'Biz Books', 'publication_year': 2023,
            'keywords': 'management business leadership strategy operations'
        },
        {
            'title': 'Microprocessor Architecture', 'author': 'James Brown',
            'isbn': '978-0-234567-05-0', 'category': 'Electronics',
            'publisher': 'Micro Press', 'publication_year': 2024,
            'keywords': 'microprocessor architecture VLSI CPU design'
        },
        {
            'title': 'Signal Processing Algorithms', 'author': 'Sarah Johnson',
            'isbn': '978-0-234567-06-0', 'category': 'Electronics',
            'publisher': 'Signal Books', 'publication_year': 2024,
            'keywords': 'signal processing algorithms DSP digital filters'
        },
        {
            'title': 'Chemistry Lab Manual', 'author': 'Lisa Wang',
            'isbn': '978-0-345678-04-0', 'category': 'Chemistry',
            'publisher': 'Chem Publications', 'publication_year': 2024,
            'keywords': 'chemistry laboratory experiments analysis techniques'
        },
        {
            'title': 'Quantum Physics', 'author': 'Kevin White',
            'isbn': '978-0-456789-02-0', 'category': 'Physics',
            'publisher': 'Engineering Physics', 'publication_year': 2024,
            'keywords': 'quantum physics mechanics particles energy'
        }
    ]
    
    # Build search index
    engine = IntelligentSearchEngine()
    engine.build_index(books)
    
    # Test various search queries
    test_queries = [
        "python programming",
        "database SQL",
        "signal processing",
        "machine learning AI",
        "chemistry experiments",
        "physics quantum",
        "microprocessor",
        "mathematics calculus",
        "web development",
        "literature poetry"
    ]
    
    print("\n" + "="*60)
    print("INTELLIGENT SEARCH DEMONSTRATION")
    print("="*60)
    
    search_results = {}
    for query in test_queries:
        results = engine.search(query, top_k=3)
        search_results[query] = results
        print(f"\nQuery: '{query}'")
        print(f"Results found: {len(results)}")
        for i, result in enumerate(results, 1):
            book = result['book']
            print(f"  {i}. {book['title']} by {book['author']}")
            print(f"     Score: {result['score']:.4f} | Category: {book['category']}")
            print(f"     Matched fields: {', '.join(result['match_fields'])}")
    
    # Search statistics
    stats = engine.get_search_statistics()
    print(f"\nSearch Index Statistics:")
    print(f"  Total books indexed: {stats['total_books']}")
    print(f"  Vocabulary size: {stats['vocabulary_size']}")
    
    return search_results, stats, engine


if __name__ == '__main__':
    results, stats, engine = demo_search()
    print("\nIntelligent search engine demonstration completed successfully.")
