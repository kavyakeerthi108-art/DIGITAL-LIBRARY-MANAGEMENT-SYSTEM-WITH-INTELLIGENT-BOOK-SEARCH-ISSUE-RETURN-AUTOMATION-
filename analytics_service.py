"""
Analytics Service Module
Generates comprehensive charts and reports for library operations analysis.
Produces visualizations for book categories, transactions, fines, and member activity.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os


def generate_category_distribution(books_data, output_path):
    """
    Generate a pie chart showing book distribution by category.
    
    Args:
        books_data: List of dicts with 'category' and 'count' keys
        output_path: File path for the output image
    """
    categories = [b['category'] for b in books_data]
    counts = [b['count'] for b in books_data]
    
    colors = ['#2196F3', '#4CAF50', '#FF9800', '#E91E63', '#9C27B0', 
              '#00BCD4', '#FF5722', '#607D8B', '#795548', '#3F51B5']
    
    fig, ax = plt.subplots(figsize=(10, 8))
    wedges, texts, autotexts = ax.pie(
        counts, labels=categories, autopct='%1.1f%%',
        colors=colors[:len(categories)], startangle=90,
        pctdistance=0.85, explode=[0.03]*len(categories)
    )
    
    # Style the text
    for text in texts:
        text.set_fontsize(11)
        text.set_fontfamily('Times New Roman')
    for autotext in autotexts:
        autotext.set_fontsize(10)
        autotext.set_fontfamily('Times New Roman')
        autotext.set_fontweight('bold')
    
    ax.set_title('Book Distribution by Category', fontsize=16, 
                 fontfamily='Times New Roman', fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Category distribution chart saved to: {output_path}")


def generate_transaction_summary(transaction_data, output_path):
    """
    Generate a stacked bar chart showing transaction types.
    
    Args:
        transaction_data: Dict with 'issued', 'returned', 'overdue' counts
        output_path: File path for the output image
    """
    labels = ['Total', 'Active', 'Returned', 'Overdue']
    counts = [
        transaction_data.get('total', 0),
        transaction_data.get('issued', 0),
        transaction_data.get('returned', 0),
        transaction_data.get('overdue', 0)
    ]
    
    colors = ['#2196F3', '#FF9800', '#4CAF50', '#E91E63']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(labels, counts, color=colors, width=0.6, edgecolor='white', linewidth=2)
    
    # Add value labels on bars
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{count}', ha='center', va='bottom', fontsize=14,
                fontweight='bold', fontfamily='Times New Roman')
    
    ax.set_ylabel('Number of Transactions', fontsize=13, fontfamily='Times New Roman')
    ax.set_title('Transaction Summary', fontsize=16,
                 fontfamily='Times New Roman', fontweight='bold', pad=15)
    ax.set_ylim(0, max(counts) * 1.2)
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Transaction summary chart saved to: {output_path}")


def generate_fine_analysis(fine_data, output_path):
    """
    Generate a bar chart showing fine distribution across membership types.
    
    Args:
        fine_data: Dict with membership types and their fine amounts
        output_path: File path for the output image
    """
    member_types = list(fine_data.keys())
    amounts = [fine_data[m]['total_fine'] for m in member_types]
    member_counts = [fine_data[m]['count'] for m in member_types]
    avg_fines = [fine_data[m]['average'] for m in member_types]
    
    x = np.arange(len(member_types))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars1 = ax.bar(x - width/2, amounts, width, label='Total Fine (Rs.)',
                   color='#FF5722', edgecolor='white', linewidth=1.5)
    bars2 = ax.bar(x + width/2, avg_fines, width, label='Average Fine (Rs.)',
                   color='#FF9800', edgecolor='white', linewidth=1.5)
    
    ax.set_xlabel('Membership Type', fontsize=13, fontfamily='Times New Roman')
    ax.set_ylabel('Fine Amount (Rs.)', fontsize=13, fontfamily='Times New Roman')
    ax.set_title('Fine Analysis by Membership Type', fontsize=16,
                 fontfamily='Times New Roman', fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(member_types, fontsize=12, fontfamily='Times New Roman')
    ax.legend(fontsize=11, loc='upper left')
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Add member count annotations
    for bar, count in zip(bars1, member_counts):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 2,
                f'n={count}', ha='center', va='bottom', fontsize=10,
                fontfamily='Times New Roman', style='italic')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Fine analysis chart saved to: {output_path}")


def generate_availability_tracking(availability_data, output_path):
    """
    Generate a horizontal bar chart showing book availability status.
    
    Args:
        availability_data: List of dicts with 'title' and 'available'/'total' keys
        output_path: File path for the output image
    """
    titles = [b['title'] for b in availability_data[:12]]
    available = [b['available'] for b in availability_data[:12]]
    total = [b['total'] for b in availability_data[:12]]
    issued = [t - a for t, a in zip(total, available)]
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    y = np.arange(len(titles))
    
    # Stacked horizontal bars
    bars1 = ax.barh(y, available, height=0.6, label='Available',
                    color='#4CAF50', edgecolor='white')
    bars2 = ax.barh(y, issued, height=0.6, left=available, label='Issued',
                    color='#F44336', edgecolor='white')
    
    # Add percentage labels
    for i, (avail, tot) in enumerate(zip(available, total)):
        pct = (avail / tot * 100) if tot > 0 else 0
        ax.text(avail + tot - tot + tot + 0.1, i, f'{pct:.0f}%', 
                va='center', fontsize=9, fontfamily='Times New Roman',
                color='white', fontweight='bold')
    
    ax.set_xlabel('Number of Copies', fontsize=13, fontfamily='Times New Roman')
    ax.set_title('Book Availability Status', fontsize=16,
                 fontfamily='Times New Roman', fontweight='bold', pad=15)
    ax.set_yticks(y)
    ax.set_yticklabels(titles, fontsize=10, fontfamily='Times New Roman')
    ax.legend(fontsize=11, loc='lower right')
    ax.grid(axis='x', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Availability tracking chart saved to: {output_path}")


def generate_monthly_trends(trend_data, output_path):
    """
    Generate a line chart showing monthly trends in library activity.
    
    Args:
        trend_data: Dict with 'months', 'issues', 'returns', 'overdue' lists
        output_path: File path for the output image
    """
    months = trend_data.get('months', [])
    issues = trend_data.get('issues', [])
    returns = trend_data.get('returns', [])
    overdue = trend_data.get('overdue', [])
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(months))
    width = 0.25
    
    ax.bar(x - width, issues, width, label='Books Issued', color='#2196F3', edgecolor='white')
    ax.bar(x, returns, width, label='Books Returned', color='#4CAF50', edgecolor='white')
    ax.bar(x + width, overdue, width, label='Overdue', color='#E91E63', edgecolor='white')
    
    # Add trend line for overdue
    ax.plot(x, overdue, 'o-', color='#E91E63', linewidth=2, alpha=0.5)
    
    ax.set_xlabel('Month', fontsize=13, fontfamily='Times New Roman')
    ax.set_ylabel('Count', fontsize=13, fontfamily='Times New Roman')
    ax.set_title('Monthly Library Activity Trends', fontsize=16,
                 fontfamily='Times New Roman', fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(months, fontsize=10, fontfamily='Times New Roman')
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Monthly trends chart saved to: {output_path}")


def generate_member_activity(member_data, output_path):
    """
    Generate a radar chart showing member activity patterns.
    
    Args:
        member_data: List of dicts with 'name', 'books_read', 'fines', 'on_time_rate'
        output_path: File path for the output image
    """
    names = [m['name'] for m in member_data[:8]]
    books_read = [m['books_read'] for m in member_data[:8]]
    fines = [m['fines'] for m in member_data[:8]]
    on_time = [m['on_time_rate'] for m in member_data[:8]]
    
    fig, ax = plt.subplots(figsize=(10, 7))
    
    x = np.arange(len(names))
    width = 0.25
    
    ax.bar(x - width, books_read, width, label='Books Read', color='#2196F3', edgecolor='white')
    ax2 = ax.twinx()
    ax2.plot(x, on_time, 'o-', color='#4CAF50', linewidth=2, label='On-Time Rate (%)')
    ax2.set_ylabel('On-Time Return Rate (%)', fontsize=12, fontfamily='Times New Roman')
    ax2.set_ylim(0, 110)
    
    ax.set_xlabel('Member Name', fontsize=13, fontfamily='Times New Roman')
    ax.set_ylabel('Number of Books', fontsize=13, fontfamily='Times New Roman')
    ax.set_title('Member Activity Profile', fontsize=16,
                 fontfamily='Times New Roman', fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=10, fontfamily='Times New Roman', rotation=15)
    
    # Combine legends
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, fontsize=11, loc='upper left')
    
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Member activity chart saved to: {output_path}")


def generate_fine_tier_analysis(fine_tier_data, output_path):
    """
    Generate a chart showing fine distribution by overdue duration tiers.
    
    Args:
        fine_tier_data: Dict with tier names and their counts/amounts
        output_path: File path for the output image
    """
    tiers = list(fine_tier_data.keys())
    counts = [fine_tier_data[t]['count'] for t in tiers]
    amounts = [fine_tier_data[t]['total_amount'] for t in tiers]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(tiers))
    width = 0.4
    
    bars1 = ax.bar(x - width/2, counts, width, label='Number of Cases',
                   color='#9C27B0', edgecolor='white')
    
    ax2 = ax.twinx()
    bars2 = ax2.bar(x + width/2, amounts, width, label='Total Fine (Rs.)',
                    color='#FF5722', edgecolor='white')
    
    ax.set_xlabel('Overdue Duration', fontsize=13, fontfamily='Times New Roman')
    ax.set_ylabel('Number of Cases', fontsize=13, fontfamily='Times New Roman', color='#9C27B0')
    ax2.set_ylabel('Total Fine Amount (Rs.)', fontsize=13, fontfamily='Times New Roman', color='#FF5722')
    ax.set_title('Fine Distribution by Overdue Tier', fontsize=16,
                 fontfamily='Times New Roman', fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(tiers, fontsize=11, fontfamily='Times New Roman')
    
    # Combine legends
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, fontsize=11, loc='upper right')
    
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Fine tier analysis chart saved to: {output_path}")


def generate_all_charts():
    """Generate all analytical charts for the report"""
    output_dir = '/home/ubuntu/library_project/reports'
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Category Distribution
    books_data = [
        {'category': 'Computer Science', 'count': 6},
        {'category': 'Electronics', 'count': 4},
        {'category': 'Chemistry', 'count': 3},
        {'category': 'Physics', 'count': 2},
        {'category': 'Mathematics', 'count': 1},
        {'category': 'Literature', 'count': 1},
        {'category': 'Psychology', 'count': 1},
        {'category': 'Economics', 'count': 1},
        {'category': 'Science', 'count': 1},
        {'category': 'Management', 'count': 1}
    ]
    generate_category_distribution(books_data, 
                                   os.path.join(output_dir, 'category_distribution.png'))
    
    # 2. Transaction Summary
    transaction_data = {
        'total': 50,
        'issued': 12,
        'returned': 35,
        'overdue': 3
    }
    generate_transaction_summary(transaction_data,
                                 os.path.join(output_dir, 'transaction_summary.png'))
    
    # 3. Fine Analysis
    fine_data = {
        'Student': {'total_fine': 850.0, 'count': 25, 'average': 34.0},
        'Faculty': {'total_fine': 120.0, 'count': 5, 'average': 24.0},
        'Staff': {'total_fine': 180.0, 'count': 8, 'average': 22.5},
        'Guest': {'total_fine': 450.0, 'count': 4, 'average': 112.5}
    }
    generate_fine_analysis(fine_data,
                           os.path.join(output_dir, 'fine_analysis.png'))
    
    # 4. Availability Tracking
    availability_data = [
        {'title': 'Python Programming', 'available': 2, 'total': 3},
        {'title': 'Data Structures', 'available': 1, 'total': 4},
        {'title': 'Machine Learning', 'available': 1, 'total': 2},
        {'title': 'Database Systems', 'available': 2, 'total': 3},
        {'title': 'Web Development', 'available': 1, 'total': 2},
        {'title': 'Operating Systems', 'available': 3, 'total': 3},
        {'title': 'Signal Processing', 'available': 1, 'total': 2},
        {'title': 'Microprocessor', 'available': 2, 'total': 3},
        {'title': 'VLSI Design', 'available': 2, 'total': 2},
        {'title': 'Organic Chemistry', 'available': 3, 'total': 4},
        {'title': 'Physics for Engineers', 'available': 2, 'total': 3},
        {'title': 'Mathematics', 'available': 4, 'total': 4}
    ]
    generate_availability_tracking(availability_data,
                                   os.path.join(output_dir, 'availability_tracking.png'))
    
    # 5. Monthly Trends
    trend_data = {
        'months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'issues': [15, 22, 18, 25, 20, 12],
        'returns': [12, 20, 16, 22, 18, 15],
        'overdue': [3, 5, 2, 4, 3, 1]
    }
    generate_monthly_trends(trend_data,
                            os.path.join(output_dir, 'monthly_trends.png'))
    
    # 6. Member Activity
    member_data = [
        {'name': 'Rahul', 'books_read': 8, 'fines': 45.0, 'on_time_rate': 85},
        {'name': 'Priya', 'books_read': 12, 'fines': 0.0, 'on_time_rate': 100},
        {'name': 'Amit', 'books_read': 5, 'fines': 80.0, 'on_time_rate': 60},
        {'name': 'Sneha', 'books_read': 10, 'fines': 20.0, 'on_time_rate': 90},
        {'name': 'Vikram', 'books_read': 15, 'fines': 0.0, 'on_time_rate': 95},
        {'name': 'Anita', 'books_read': 6, 'fines': 35.0, 'on_time_rate': 75},
        {'name': 'Manoj', 'books_read': 9, 'fines': 55.0, 'on_time_rate': 70},
        {'name': 'Kavita', 'books_read': 7, 'fines': 10.0, 'on_time_rate': 92}
    ]
    generate_member_activity(member_data,
                             os.path.join(output_dir, 'member_activity.png'))
    
    # 7. Fine Tier Analysis
    fine_tier_data = {
        '1-7 Days': {'count': 15, 'total_amount': 150.0},
        '8-14 Days': {'count': 8, 'total_amount': 240.0},
        '15-30 Days': {'count': 5, 'total_amount': 350.0},
        '30+ Days': {'count': 2, 'total_amount': 450.0}
    }
    generate_fine_tier_analysis(fine_tier_data,
                                os.path.join(output_dir, 'fine_tier_analysis.png'))
    
    # Copy charts to screenshots directory
    screenshots_dir = '/home/ubuntu/library_project/screenshots'
    os.makedirs(screenshots_dir, exist_ok=True)
    
    import shutil
    for f in os.listdir(output_dir):
        if f.endswith('.png'):
            shutil.copy2(os.path.join(output_dir, f), screenshots_dir)
    
    print("\nAll 7 analytical charts generated successfully!")
    print(f"Charts saved in: {output_dir}")
    print(f"Screenshots saved in: {screenshots_dir}")


if __name__ == '__main__':
    generate_all_charts()
