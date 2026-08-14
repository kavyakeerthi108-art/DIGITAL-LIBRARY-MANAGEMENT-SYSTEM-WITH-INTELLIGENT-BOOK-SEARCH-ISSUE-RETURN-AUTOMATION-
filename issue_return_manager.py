"""
Issue-Return Automation Module
Handles the complete lifecycle of book borrowing and returning,
including real-time inventory updates, transaction tracking, and notifications.
"""

from datetime import datetime, timedelta
import json


class IssueReturnManager:
    """
    Manages the complete issue-return lifecycle for library books.
    Tracks transactions, updates inventory in real-time, and generates
    notifications for all key events.
    """
    
    def __init__(self, loan_period=14, max_books_per_member=5):
        """
        Initialize the issue-return manager.
        
        Args:
            loan_period: Default loan period in days
            max_books_per_member: Maximum books a member can borrow
        """
        self.loan_period = loan_period
        self.max_books_per_member = max_books_per_member
        self.transactions = []
        self.inventory = {}  # book_id -> available_copies
        self.member_records = {}  # member_id -> {'books_issued': int, 'fine_total': float}
    
    def issue_book(self, book_id, book_title, member_id, member_name, 
                   loan_days=None, issue_date=None):
        """
        Issue a book to a member.
        
        Args:
            book_id: Unique book identifier
            book_title: Title of the book
            member_id: Unique member identifier
            member_name: Name of the member
            loan_days: Loan period in days (optional)
            issue_date: Date of issue (optional, defaults to today)
            
        Returns:
            Transaction record with full details
        """
        if issue_date is None:
            issue_date = datetime.utcnow().date()
        
        if loan_days is None:
            loan_days = self.loan_period
        
        due_date = issue_date + timedelta(days=loan_days)
        
        # Initialize member record if not exists
        if member_id not in self.member_records:
            self.member_records[member_id] = {
                'name': member_name,
                'books_issued': 0,
                'fine_total': 0.0,
                'status': 'active'
            }
        
        # Check member eligibility
        member = self.member_records[member_id]
        if member['books_issued'] >= self.max_books_per_member:
            return {
                'success': False,
                'error': f'Member has reached maximum limit of {self.max_books_per_member} books',
                'member': member_name
            }
        
        if member['status'] == 'suspended':
            return {
                'success': False,
                'error': 'Member account is suspended due to overdue fines',
                'member': member_name
            }
        
        # Initialize inventory if not exists
        if book_id not in self.inventory:
            self.inventory[book_id] = {
                'title': book_title,
                'total_copies': 1,
                'available_copies': 1
            }
        
        # Check book availability
        if self.inventory[book_id]['available_copies'] <= 0:
            return {
                'success': False,
                'error': f'No copies available for "{book_title}"',
                'book': book_title
            }
        
        # Create transaction
        transaction_id = len(self.transactions) + 1
        transaction = {
            'id': transaction_id,
            'book_id': book_id,
            'book_title': book_title,
            'member_id': member_id,
            'member_name': member_name,
            'issue_date': issue_date,
            'due_date': due_date,
            'loan_days': loan_days,
            'return_date': None,
            'fine_amount': 0.0,
            'status': 'issued',
            'is_overdue': False
        }
        
        # Update inventory
        self.inventory[book_id]['available_copies'] -= 1
        
        # Update member record
        member['books_issued'] += 1
        
        self.transactions.append(transaction)
        
        notification = (f"Book '{book_title}' issued to {member_name}.\n"
                       f"Issue Date: {issue_date}\n"
                       f"Due Date: {due_date}\n"
                       f"Loan Period: {loan_days} days\n"
                       f"Transaction ID: {transaction_id}")
        
        return {
            'success': True,
            'transaction': transaction,
            'notification': notification
        }
    
    def return_book(self, transaction_id, return_date=None):
        """
        Process a book return.
        
        Args:
            transaction_id: The ID of the original issue transaction
            return_date: Date of return (optional, defaults to today)
            
        Returns:
            Return result with fine calculation
        """
        if return_date is None:
            return_date = datetime.utcnow().date()
        
        # Find the transaction
        transaction = None
        for t in self.transactions:
            if t['id'] == transaction_id and t['status'] == 'issued':
                transaction = t
                break
        
        if not transaction:
            return {
                'success': False,
                'error': 'Transaction not found or book already returned'
            }
        
        # Calculate overdue days and fine
        days_overdue = max(0, (return_date - transaction['due_date']).days)
        fine_per_day = 5.0
        grace_period = 3
        effective_days = max(0, days_overdue - grace_period)
        fine_amount = effective_days * fine_per_day
        
        # Update transaction
        transaction['return_date'] = return_date
        transaction['fine_amount'] = fine_amount
        transaction['status'] = 'returned'
        transaction['days_overdue'] = days_overdue
        
        # Update inventory
        book_id = transaction['book_id']
        if book_id in self.inventory:
            self.inventory[book_id]['available_copies'] += 1
        
        # Update member record
        member_id = transaction['member_id']
        if member_id in self.member_records:
            member = self.member_records[member_id]
            member['books_issued'] = max(0, member['books_issued'] - 1)
            member['fine_total'] += fine_amount
        
        notification = (f"Book '{transaction['book_title']}' returned by {transaction['member_name']}.\n"
                       f"Return Date: {return_date}\n"
                       f"Days Overdue: {days_overdue}\n"
                       f"Fine Amount: Rs. {fine_amount}\n"
                       f"Transaction ID: {transaction_id}")
        
        return {
            'success': True,
            'transaction': transaction,
            'days_overdue': days_overdue,
            'fine_amount': fine_amount,
            'notification': notification
        }
    
    def check_overdue_books(self, as_of_date=None):
        """
        Check for overdue books as of a specific date.
        
        Args:
            as_of_date: Date to check against (optional, defaults to today)
            
        Returns:
            List of overdue transactions
        """
        if as_of_date is None:
            as_of_date = datetime.utcnow().date()
        
        overdue = []
        for t in self.transactions:
            if t['status'] == 'issued' and t['due_date'] < as_of_date:
                days_overdue = (as_of_date - t['due_date']).days
                t['is_overdue'] = True
                t['days_overdue'] = days_overdue
                fine_amount = max(0, days_overdue - 3) * 5.0
                t['accumulated_fine'] = fine_amount
                overdue.append(t)
        
        return overdue
    
    def get_member_history(self, member_id):
        """
        Get complete borrowing history for a member.
        
        Args:
            member_id: Member identifier
            
        Returns:
            Member history with statistics
        """
        member_transactions = [t for t in self.transactions if t['member_id'] == member_id]
        
        if not member_transactions:
            return {'member_id': member_id, 'transactions': [], 'stats': {}}
        
        issued = [t for t in member_transactions if t['status'] == 'issued']
        returned = [t for t in member_transactions if t['status'] == 'returned']
        overdue = [t for t in member_transactions if t.get('is_overdue', False)]
        
        total_fine = sum(t.get('fine_amount', 0) for t in member_transactions)
        avg_loan_days = 0
        if returned:
            avg_loan_days = sum(
                (t['return_date'] - t['issue_date']).days if t['return_date']
                else (datetime.utcnow().date() - t['issue_date']).days
                for t in returned
            ) / len(returned)
        
        return {
            'member_id': member_id,
            'member_name': self.member_records.get(member_id, {}).get('name', 'Unknown'),
            'total_transactions': len(member_transactions),
            'currently_issued': len(issued),
            'returned': len(returned),
            'overdue': len(overdue),
            'total_fine': round(total_fine, 2),
            'avg_loan_days': round(avg_loan_days, 1),
            'transactions': member_transactions
        }
    
    def get_library_statistics(self):
        """Generate comprehensive library statistics"""
        total_transactions = len(self.transactions)
        issued = [t for t in self.transactions if t['status'] == 'issued']
        returned = [t for t in self.transactions if t['status'] == 'returned']
        overdue = [t for t in self.transactions if t.get('is_overdue', False)]
        
        total_fines = sum(t.get('fine_amount', 0) for t in self.transactions)
        
        # Books in inventory
        total_copies = sum(inv['total_copies'] for inv in self.inventory.values())
        available = sum(inv['available_copies'] for inv in self.inventory.values())
        issued_copies = total_copies - available
        
        # Active members
        active_members = sum(1 for m in self.member_records.values() 
                           if m['books_issued'] > 0)
        
        return {
            'total_transactions': total_transactions,
            'currently_issued': len(issued),
            'returned': len(returned),
            'overdue_count': len(overdue),
            'total_fines_collected': round(total_fines, 2),
            'total_book_copies': total_copies,
            'available_copies': available,
            'issued_copies': issued_copies,
            'total_members': len(self.member_records),
            'active_members': active_members,
            'inventory': dict(self.inventory),
            'member_records': dict(self.member_records)
        }


def demo_issue_return():
    """Demonstrate the issue-return automation capabilities"""
    manager = IssueReturnManager(loan_period=14, max_books_per_member=5)
    
    print("="*60)
    print("ISSUE-RETURN AUTOMATION DEMONSTRATION")
    print("="*60)
    
    # Issue books
    books = [
        (1, 'Python Programming'),
        (2, 'Data Structures'),
        (3, 'Machine Learning'),
        (4, 'Database Systems'),
        (5, 'Web Development')
    ]
    
    members = [
        ('MEM001', 'Rahul Sharma'),
        ('MEM002', 'Priya Patel'),
        ('MEM003', 'Amit Kumar')
    ]
    
    # Issue multiple books
    print("\n--- Issuing Books ---")
    for book_id, title in books[:3]:
        result = manager.issue_book(book_id, title, 'MEM001', 'Rahul Sharma')
        if result['success']:
            print(f"  Issued: {title} -> {result['notification']}")
        else:
            print(f"  Failed: {result['error']}")
    
    result = manager.issue_book(1, 'Digital Signal Processing', 'MEM002', 'Priya Patel')
    if result['success']:
        print(f"  Issued: Digital Signal Processing -> {result['notification']}")
    
    result = manager.issue_book(3, 'Organic Chemistry', 'MEM003', 'Amit Kumar')
    if result['success']:
        print(f"  Issued: Organic Chemistry -> {result['notification']}")
    
    # Return books (some on time, some overdue)
    print("\n--- Returning Books ---")
    # Return transaction 1 on time
    result = manager.return_book(1, datetime(2025, 1, 28).date())
    print(f"  Return ID 1: {result['notification']}")
    
    # Return transaction 2 late
    result = manager.return_book(2, datetime(2025, 2, 5).date())
    print(f"  Return ID 2: {result['notification']}")
    
    # Return transaction 3 very late
    result = manager.return_book(3, datetime(2025, 2, 15).date())
    print(f"  Return ID 3: {result['notification']}")
    
    # Return transaction 4 on time
    result = manager.return_book(4, datetime(2025, 1, 25).date())
    if result['success']:
        print(f"  Return ID 4: {result['notification']}")
    else:
        print(f"  Return ID 4: {result.get('error', 'Already returned')}")
    
    # Check overdue books
    print("\n--- Overdue Check (as of 2025-02-10) ---")
    overdue = manager.check_overdue_books(datetime(2025, 2, 10).date())
    for book in overdue:
        print(f"  Overdue: {book['book_title']} | Days: {book['days_overdue']} | Fine: Rs. {book.get('accumulated_fine', 0)}")
    
    if not overdue:
        print("  No overdue books found.")
    
    # Get library statistics
    print("\n--- Library Statistics ---")
    stats = manager.get_library_statistics()
    print(f"  Total Transactions: {stats['total_transactions']}")
    print(f"  Currently Issued: {stats['currently_issued']}")
    print(f"  Returned: {stats['returned']}")
    print(f"  Overdue: {stats['overdue_count']}")
    print(f"  Total Fines: Rs. {stats['total_fines_collected']}")
    print(f"  Available Copies: {stats['available_copies']}")
    print(f"  Active Members: {stats['active_members']}")
    
    # Get member history
    print("\n--- Member History (MEM001 - Rahul Sharma) ---")
    history = manager.get_member_history('MEM001')
    print(f"  Total Transactions: {history['total_transactions']}")
    print(f"  Returned: {history['returned']}")
    print(f"  Currently Issued: {history['currently_issued']}")
    print(f"  Total Fine: Rs. {history['total_fine']}")
    
    return stats, manager


if __name__ == '__main__':
    stats, manager = demo_issue_return()
    print("\nIssue-return automation demonstration completed successfully.")
