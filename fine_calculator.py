"""
Fine Calculation Engine
Implements automatic overdue fine calculation based on library policies.
Supports configurable fine rates, grace periods, and membership-based policies.
"""

from datetime import datetime, timedelta
import json


class FineCalculator:
    """
    Calculates overdue fines based on configurable library policies.
    Supports different fine rates for different membership types and
    implements grace periods, maximum fine caps, and tiered fine structures.
    """
    
    def __init__(self, config=None):
        """
        Initialize the fine calculator with optional configuration.
        
        Args:
            config: Dictionary with fine policy configuration
        """
        self.config = config or {}
        self.fine_per_day = self.config.get('fine_per_day', 5.0)
        self.grace_period = self.config.get('grace_period', 3)
        self.max_fine_per_book = self.config.get('max_fine_per_book', 500.0)
        self.max_fine_per_member = self.config.get('max_fine_per_member', 2000.0)
        
        # Membership-based fine rates
        self.membership_fine_rates = {
            'student': 1.0,      # 100% of standard rate
            'faculty': 0.5,      # 50% discount for faculty
            'staff': 0.75,       # 25% discount for staff
            'guest': 1.5         # 50% surcharge for guest members
        }
        
        # Tiered fine structure (progressive fines)
        self.tiered_fines = self.config.get('tiered_fines', [
            {'days': 7, 'rate_multiplier': 1.0},    # First 7 days: standard rate
            {'days': 14, 'rate_multiplier': 1.5},   # Days 8-14: 1.5x rate
            {'days': 30, 'rate_multiplier': 2.0},   # Days 15-30: 2x rate
            {'days': 999, 'rate_multiplier': 3.0}   # Beyond 30 days: 3x rate
        ])
    
    def calculate_fine(self, due_date, return_date, membership_type='student'):
        """
        Calculate the fine for an overdue book.
        
        Args:
            due_date: The date the book was due (datetime or string)
            return_date: The date the book was returned (datetime or string)
            membership_type: Type of library member
            
        Returns:
            Dictionary with fine calculation details
        """
        # Convert strings to dates if necessary
        if isinstance(due_date, str):
            due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
        if isinstance(return_date, str):
            return_date = datetime.strptime(return_date, '%Y-%m-%d').date()
        
        # Calculate days overdue
        if return_date <= due_date:
            return {
                'fine_amount': 0.0,
                'days_overdue': 0,
                'grace_days_used': 0,
                'effective_days': 0,
                'rate_applied': 0.0,
                'membership_discount': 1.0,
                'is_overdue': False,
                'message': 'Book returned on time. No fine applicable.'
            }
        
        days_overdue = (return_date - due_date).days
        
        # Apply grace period
        effective_days = max(0, days_overdue - self.grace_period)
        
        if effective_days == 0:
            return {
                'fine_amount': 0.0,
                'days_overdue': days_overdue,
                'grace_days_used': days_overdue,
                'effective_days': 0,
                'rate_applied': 0.0,
                'membership_discount': 1.0,
                'is_overdue': False,
                'message': f'Book returned within grace period ({self.grace_period} days). No fine.'
            }
        
        # Apply tiered fine structure
        total_fine = 0.0
        day_counter = 0
        fine_breakdown = []
        
        for tier in self.tiered_fines:
            tier_days = min(effective_days, tier['days']) - day_counter
            if tier_days <= 0:
                break
            
            tier_rate = self.fine_per_day * tier['rate_multiplier']
            tier_fine = tier_days * tier_rate
            total_fine += tier_fine
            
            fine_breakdown.append({
                'period': f'Days {day_counter + 1}-{day_counter + tier_days}',
                'days': tier_days,
                'rate_per_day': tier_rate,
                'fine': tier_fine
            })
            
            day_counter += tier_days
        
        # Apply membership discount
        membership_discount = self.membership_fine_rates.get(membership_type, 1.0)
        discounted_fine = total_fine * membership_discount
        
        # Apply fine caps
        discounted_fine = min(discounted_fine, self.max_fine_per_book)
        
        return {
            'fine_amount': round(discounted_fine, 2),
            'days_overdue': days_overdue,
            'grace_days_used': self.grace_period if days_overdue >= self.grace_period else days_overdue,
            'effective_days': effective_days,
            'base_rate': self.fine_per_day,
            'membership_discount': membership_discount,
            'is_overdue': True,
            'fine_breakdown': fine_breakdown,
            'raw_fine': round(total_fine, 2),
            'message': f'Overdue by {days_overdue} days. Fine: Rs. {discounted_fine}'
        }
    
    def calculate_fine_simple(self, due_date, return_date):
        """Simple fine calculation without tiered structure."""
        if isinstance(due_date, str):
            due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
        if isinstance(return_date, str):
            return_date = datetime.strptime(return_date, '%Y-%m-%d').date()
        
        if return_date <= due_date:
            return 0.0
        
        days_overdue = (return_date - due_date).days
        effective_days = max(0, days_overdue - self.grace_period)
        
        return round(effective_days * self.fine_per_day, 2)
    
    def generate_fine_report(self, transactions, membership_types=None):
        """
        Generate a comprehensive fine report for a set of transactions.
        
        Args:
            transactions: List of transaction dicts with due_date, return_date
            membership_types: List of membership types for each transaction
            
        Returns:
            Dictionary with fine statistics and details
        """
        if not transactions:
            return {'total_fine': 0.0, 'transactions': []}
        
        if membership_types is None:
            membership_types = ['student'] * len(transactions)
        
        total_fine = 0.0
        overdue_count = 0
        fine_details = []
        
        for i, transaction in enumerate(transactions):
            member_type = membership_types[i] if i < len(membership_types) else 'student'
            result = self.calculate_fine(
                transaction.get('due_date'),
                transaction.get('return_date'),
                member_type
            )
            
            fine_details.append({
                'transaction_id': i + 1,
                'due_date': str(transaction['due_date']),
                'return_date': str(transaction['return_date']),
                'days_overdue': result['days_overdue'],
                'fine_amount': result['fine_amount'],
                'is_overdue': result['is_overdue'],
                'membership_type': member_type
            })
            
            total_fine += result['fine_amount']
            if result['is_overdue']:
                overdue_count += 1
        
        return {
            'total_fine': round(total_fine, 2),
            'overdue_count': overdue_count,
            'total_transactions': len(transactions),
            'on_time_percentage': round((1 - overdue_count / len(transactions)) * 100, 1),
            'average_fine': round(total_fine / len(transactions), 2),
            'max_fine': round(max(d['fine_amount'] for d in fine_details), 2),
            'fine_details': fine_details
        }
    
    def get_policy_summary(self):
        """Return a summary of the fine policy configuration."""
        return {
            'fine_per_day': self.fine_per_day,
            'grace_period_days': self.grace_period,
            'max_fine_per_book': self.max_fine_per_book,
            'max_fine_per_member': self.max_fine_per_member,
            'membership_rates': self.membership_fine_rates,
            'tiered_fines': self.tiered_fines
        }


def demo_fine_calculation():
    """Demonstrate the fine calculation capabilities"""
    calculator = FineCalculator()
    
    print("="*60)
    print("FINE CALCULATION DEMONSTRATION")
    print("="*60)
    
    # Test cases: (due_date, return_date, membership_type)
    test_cases = [
        ('2025-01-15', '2025-01-14', 'student'),   # Returned early
        ('2025-01-15', '2025-01-15', 'student'),   # Returned on time
        ('2025-01-15', '2025-01-16', 'student'),   # 1 day late (within grace)
        ('2025-01-15', '2025-01-18', 'student'),   # 3 days late (within grace)
        ('2025-01-15', '2025-01-20', 'student'),   # 5 days late (2 effective)
        ('2025-01-15', '2025-01-25', 'student'),   # 10 days late (7 effective)
        ('2025-01-15', '2025-02-01', 'student'),   # 17 days late (14 effective)
        ('2025-01-15', '2025-02-15', 'student'),   # 31 days late (28 effective)
        ('2025-01-15', '2025-01-25', 'faculty'),   # Faculty discount
        ('2025-01-15', '2025-02-01', 'staff'),     # Staff discount
    ]
    
    results = []
    for due, ret, mtype in test_cases:
        result = calculator.calculate_fine(due, ret, mtype)
        results.append(result)
        print(f"\nDue: {due} | Return: {ret} | Type: {mtype}")
        print(f"  Days overdue: {result['days_overdue']}")
        print(f"  Effective days (after grace): {result['effective_days']}")
        print(f"  Fine: Rs. {result['fine_amount']}")
        print(f"  Message: {result['message']}")
    
    # Generate fine report
    transactions = [
        {'due_date': '2025-01-15', 'return_date': '2025-01-14'},
        {'due_date': '2025-01-15', 'return_date': '2025-01-20'},
        {'due_date': '2025-01-15', 'return_date': '2025-01-25'},
        {'due_date': '2025-01-15', 'return_date': '2025-02-01'},
        {'due_date': '2025-01-15', 'return_date': '2025-02-15'},
        {'due_date': '2025-01-15', 'return_date': '2025-01-15'},
        {'due_date': '2025-01-15', 'return_date': '2025-01-18'},
        {'due_date': '2025-01-15', 'return_date': '2025-02-10'},
        {'due_date': '2025-01-15', 'return_date': '2025-01-30'},
        {'due_date': '2025-01-15', 'return_date': '2025-02-20'},
    ]
    member_types = ['student', 'student', 'student', 'faculty', 'student',
                    'student', 'student', 'staff', 'student', 'student']
    
    report = calculator.generate_fine_report(transactions, member_types)
    print(f"\n{'='*60}")
    print("FINE REPORT SUMMARY")
    print(f"{'='*60}")
    print(f"Total Transactions: {report['total_transactions']}")
    print(f"Overdue Books: {report['overdue_count']}")
    print(f"On-Time Return Rate: {report['on_time_percentage']}%")
    print(f"Total Fine Collected: Rs. {report['total_fine']}")
    print(f"Average Fine: Rs. {report['average_fine']}")
    print(f"Maximum Fine: Rs. {report['max_fine']}")
    
    # Policy summary
    print(f"\n{'='*60}")
    print("FINE POLICY SUMMARY")
    print(f"{'='*60}")
    policy = calculator.get_policy_summary()
    for key, value in policy.items():
        print(f"  {key}: {value}")
    
    return results, report


if __name__ == '__main__':
    results, report = demo_fine_calculation()
    print("\nFine calculation engine demonstration completed successfully.")
