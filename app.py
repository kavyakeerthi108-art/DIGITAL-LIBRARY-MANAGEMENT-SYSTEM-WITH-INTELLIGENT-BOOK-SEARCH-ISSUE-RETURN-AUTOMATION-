"""
Digital Library Management System
Main Flask Application with intelligent book search, issue-return automation,
and automatic fine calculation.
"""

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'library_secret_key_2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ============ DATABASE MODELS ============

class Member(db.Model):
    """Student/Library Member model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    member_id = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    membership_type = db.Column(db.String(20), default='student')  # student, faculty, staff
    department = db.Column(db.String(50))
    join_date = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, suspended
    books_issued = db.Column(db.Integer, default=0)
    total_fines = db.Column(db.Float, default=0.0)
    issued_books = db.relationship('Transaction', backref='member', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'member_id': self.member_id,
            'email': self.email,
            'membership_type': self.membership_type,
            'department': self.department,
            'books_issued': self.books_issued,
            'total_fines': self.total_fines,
            'status': self.status
        }


class Book(db.Model):
    """Book catalog model"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    publisher = db.Column(db.String(100))
    publication_year = db.Column(db.Integer)
    total_copies = db.Column(db.Integer, default=1)
    available_copies = db.Column(db.Integer, default=1)
    location = db.Column(db.String(50))  # shelf/rack number
    price = db.Column(db.Float, default=0.0)
    keywords = db.Column(db.Text)  # searchable keywords
    added_date = db.Column(db.Date, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'isbn': self.isbn,
            'category': self.category,
            'publisher': self.publisher,
            'publication_year': self.publication_year,
            'total_copies': self.total_copies,
            'available_copies': self.available_copies,
            'location': self.location
        }


class Transaction(db.Model):
    """Book issue/return transaction model"""
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    issue_date = db.Column(db.Date, default=datetime.utcnow)
    due_date = db.Column(db.Date)
    return_date = db.Column(db.Date)
    fine_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='issued')  # issued, returned, overdue
    notes = db.Column(db.Text)
    
    book = db.relationship('Book', backref='transactions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'book_title': self.book.title if self.book else 'Unknown',
            'book_isbn': self.book.isbn if self.book else 'N/A',
            'member_name': self.member.name if self.member else 'Unknown',
            'issue_date': str(self.issue_date),
            'due_date': str(self.due_date),
            'return_date': str(self.return_date) if self.return_date else None,
            'fine_amount': self.fine_amount,
            'status': self.status
        }


# ============ LIBRARY POLICY CONSTANTS ============

MAX_BOOKS_PER_MEMBER = 5  # Maximum books a member can borrow
DEFAULT_LOAN_PERIOD = 14  # days
FINE_PER_DAY = 5.0  # INR per day overdue
FINE_GRACE_PERIOD = 3  # grace period days after due date


# ============ ROUTES ============

@app.route('/')
def home():
    """Home page with library statistics"""
    total_books = Book.query.count()
    total_members = Member.query.count()
    active_transactions = Transaction.query.filter_by(status='issued').count()
    overdue_books = Transaction.query.filter_by(status='overdue').count()
    total_categories = db.session.query(Book.category).distinct().count()
    
    stats = {
        'total_books': total_books,
        'total_members': total_members,
        'active_transactions': active_transactions,
        'overdue_books': overdue_books,
        'total_categories': total_categories
    }
    return render_template('index.html', stats=stats)


@app.route('/search', methods=['GET', 'POST'])
def search_books():
    """Intelligent book search by title, author, category, ISBN, or keywords"""
    results = []
    query = request.args.get('q', '')
    
    if query:
        query_lower = query.lower()
        books = Book.query.all()
        for book in books:
            score = 0
            # Title match (highest weight)
            if query_lower in book.title.lower():
                score += 100
            # Author match
            if query_lower in book.author.lower():
                score += 80
            # ISBN match
            if query_lower in book.isbn.lower():
                score += 90
            # Category match
            if query_lower in book.category.lower():
                score += 70
            # Publisher match
            if book.publisher and query_lower in book.publisher.lower():
                score += 50
            # Keywords match
            if book.keywords and query_lower in book.keywords.lower():
                score += 60
            
            if score > 0:
                book_data = book.to_dict()
                book_data['relevance_score'] = score
                results.append(book_data)
        
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({'query': query, 'results': results})
    
    return render_template('search.html', results=results, query=query)


@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for intelligent book search"""
    data = request.get_json()
    query = data.get('query', '')
    filters = data.get('filters', {})
    
    results = []
    query_lower = query.lower()
    books = Book.query.all()
    
    for book in books:
        score = 0
        if query_lower in book.title.lower():
            score += 100
        if query_lower in book.author.lower():
            score += 80
        if query_lower in book.isbn.lower():
            score += 90
        if query_lower in book.category.lower():
            score += 70
        if book.publisher and query_lower in book.publisher.lower():
            score += 50
        if book.keywords and query_lower in book.keywords.lower():
            score += 60
        
        # Apply filters
        if filters.get('category') and filters['category'] != book.category:
            continue
        if filters.get('available_only') and book.available_copies <= 0:
            continue
        
        if score > 0:
            book_data = book.to_dict()
            book_data['relevance_score'] = score
            results.append(book_data)
    
    results.sort(key=lambda x: x['relevance_score'], reverse=True)
    return jsonify({'query': query, 'total_results': len(results), 'results': results[:50]})


@app.route('/member/register', methods=['GET', 'POST'])
def register_member():
    """Register a new library member"""
    if request.method == 'POST':
        name = request.form.get('name')
        member_id = request.form.get('member_id')
        email = request.form.get('email')
        phone = request.form.get('phone', '')
        membership_type = request.form.get('membership_type', 'student')
        department = request.form.get('department', '')
        
        # Check if member already exists
        existing = Member.query.filter_by(member_id=member_id).first()
        if existing:
            return jsonify({'error': 'Member ID already exists'}), 400
        
        existing_email = Member.query.filter_by(email=email).first()
        if existing_email:
            return jsonify({'error': 'Email already registered'}), 400
        
        new_member = Member(
            name=name,
            member_id=member_id,
            email=email,
            phone=phone,
            membership_type=membership_type,
            department=department,
            join_date=datetime.utcnow().date()
        )
        
        db.session.add(new_member)
        db.session.commit()
        
        return jsonify({
            'message': 'Member registered successfully',
            'member': new_member.to_dict()
        })
    
    return render_template('register_member.html')


@app.route('/book/add', methods=['POST'])
def add_book():
    """Add a new book to the catalog"""
    data = request.get_json()
    
    required_fields = ['title', 'author', 'isbn', 'category']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Check if ISBN already exists
    existing = Book.query.filter_by(isbn=data['isbn']).first()
    if existing:
        return jsonify({'error': 'ISBN already exists in catalog'}), 400
    
    new_book = Book(
        title=data['title'],
        author=data['author'],
        isbn=data['isbn'],
        category=data['category'],
        publisher=data.get('publisher', ''),
        publication_year=data.get('publication_year', 0),
        total_copies=data.get('total_copies', 1),
        available_copies=data.get('total_copies', 1),
        location=data.get('location', ''),
        price=data.get('price', 0.0),
        keywords=data.get('keywords', '')
    )
    
    db.session.add(new_book)
    db.session.commit()
    
    return jsonify({
        'message': 'Book added successfully',
        'book': new_book.to_dict()
    })


@app.route('/book/issue', methods=['POST'])
def issue_book():
    """Issue a book to a member"""
    data = request.get_json()
    book_id = data.get('book_id')
    member_id = data.get('member_id')
    loan_days = data.get('loan_days', DEFAULT_LOAN_PERIOD)
    
    book = Book.query.get(book_id)
    member = Member.query.get(member_id)
    
    if not book or not member:
        return jsonify({'error': 'Book or member not found'}), 404
    
    if book.available_copies <= 0:
        return jsonify({'error': 'No copies available for this book'}), 400
    
    if member.books_issued >= MAX_BOOKS_PER_MEMBER:
        return jsonify({'error': f'Member has reached maximum limit of {MAX_BOOKS_PER_MEMBER} books'}), 400
    
    if member.status == 'suspended':
        return jsonify({'error': 'Member account is suspended'}), 400
    
    # Create transaction
    issue_date = datetime.utcnow().date()
    due_date = issue_date + timedelta(days=loan_days)
    
    transaction = Transaction(
        book_id=book_id,
        member_id=member_id,
        issue_date=issue_date,
        due_date=due_date,
        status='issued'
    )
    
    # Update book availability
    book.available_copies -= 1
    
    # Update member record
    member.books_issued += 1
    
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({
        'message': 'Book issued successfully',
        'transaction': transaction.to_dict(),
        'due_date': str(due_date),
        'notification': f'Book "{book.title}" has been issued to {member.name}. Due date: {due_date}'
    })


@app.route('/book/return', methods=['POST'])
def return_book():
    """Return a book and calculate fines"""
    data = request.get_json()
    transaction_id = data.get('transaction_id')
    return_date_str = data.get('return_date')
    
    if return_date_str:
        return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()
    else:
        return_date = datetime.utcnow().date()
    
    transaction = Transaction.query.get(transaction_id)
    if not transaction:
        return jsonify({'error': 'Transaction not found'}), 404
    
    if transaction.status in ['returned', 'closed']:
        return jsonify({'error': 'Book already returned'}), 400
    
    book = Book.query.get(transaction.book_id)
    member = Member.query.get(transaction.member_id)
    
    # Calculate fine
    fine_amount = calculate_fine(transaction.due_date, return_date)
    
    # Update transaction
    transaction.return_date = return_date
    transaction.fine_amount = fine_amount
    transaction.status = 'returned'
    
    # Update book availability
    if book:
        book.available_copies += 1
    
    # Update member record
    if member:
        member.books_issued = max(0, member.books_issued - 1)
        member.total_fines += fine_amount
    
    db.session.commit()
    
    return jsonify({
        'message': 'Book returned successfully',
        'transaction': transaction.to_dict(),
        'fine_amount': fine_amount,
        'days_overdue': max(0, (return_date - transaction.due_date).days),
        'notification': f'Book "{book.title if book else "Unknown"}" returned. Fine: Rs. {fine_amount}'
    })


@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard with comprehensive analytics"""
    # Book statistics
    total_books = Book.query.count()
    total_copies = db.session.query(db.func.sum(Book.total_copies)).scalar() or 0
    available_copies = db.session.query(db.func.sum(Book.available_copies)).scalar() or 0
    issued_copies = total_copies - available_copies
    
    # Category breakdown
    categories = db.session.query(Book.category, db.func.count(Book.id)).group_by(Book.category).all()
    
    # Transaction statistics
    total_transactions = Transaction.query.count()
    active_transactions = Transaction.query.filter_by(status='issued').count()
    overdue_transactions = Transaction.query.filter_by(status='overdue').count()
    total_fines = db.session.query(db.func.sum(Transaction.fine_amount)).scalar() or 0
    
    # Member statistics
    total_members = Member.query.count()
    active_members = Member.query.filter_by(status='active').count()
    
    # Most borrowed books
    popular_books = db.session.query(
        Book.title, Book.author,
        db.func.count(Transaction.id).label('borrow_count')
    ).join(Transaction).group_by(Book.id).order_by(db.desc('borrow_count')).limit(10).all()
    
    return jsonify({
        'total_books': total_books,
        'total_copies': total_copies,
        'available_copies': available_copies,
        'issued_copies': issued_copies,
        'categories': [{'category': c[0], 'count': c[1]} for c in categories],
        'total_transactions': total_transactions,
        'active_transactions': active_transactions,
        'overdue_transactions': overdue_transactions,
        'total_fines': total_fines,
        'total_members': total_members,
        'active_members': active_members,
        'popular_books': [{'title': b[0], 'author': b[1], 'borrow_count': b[2]} for b in popular_books]
    })


@app.route('/admin/reports/overdue')
def overdue_report():
    """Generate overdue books report"""
    today = datetime.utcnow().date()
    overdue = Transaction.query.filter(
        Transaction.due_date < today,
        Transaction.status.in_(['issued', 'overdue'])
    ).all()
    
    for t in overdue:
        t.status = 'overdue'
        t.fine_amount = calculate_fine(t.due_date, today)
    
    db.session.commit()
    
    return jsonify({
        'total_overdue': len(overdue),
        'total_fines_pending': sum(t.fine_amount for t in overdue),
        'overdue_books': [t.to_dict() for t in overdue]
    })


# ============ FINE CALCULATION ENGINE ============

def calculate_fine(due_date, return_date):
    """
    Calculate overdue fine based on library policy.
    Fines are calculated with a grace period and daily rate.
    """
    if return_date <= due_date:
        return 0.0
    
    days_overdue = (return_date - due_date).days
    
    # Apply grace period
    effective_days = max(0, days_overdue - FINE_GRACE_PERIOD)
    
    # Calculate fine
    fine = effective_days * FINE_PER_DAY
    
    return round(fine, 2)


# ============ NOTIFICATION ENGINE ============

def generate_notification(transaction, event_type):
    """Generate notification messages for library events"""
    book = transaction.book
    member = transaction.member
    
    notifications = {
        'issue': f'Book "{book.title}" has been issued to {member.name}. Due date: {transaction.due_date}',
        'return': f'Book "{book.title}" has been returned by {member.name}. Fine: Rs. {transaction.fine_amount}',
        'overdue': f'ALERT: Book "{book.title}" is overdue! Borrower: {member.name}. Fine accumulating at Rs. {FINE_PER_DAY}/day',
        'fine_warning': f'Warning: {member.name} has accumulated Rs. {member.total_fines} in fines. Account may be suspended.',
        'due_reminder': f'Reminder: "{book.title}" is due on {transaction.due_date}. Please return on time.'
    }
    
    return notifications.get(event_type, 'Unknown event')


# ============ INITIALIZE DATABASE ============

def init_db():
    """Initialize database with sample data"""
    db.create_all()
    
    # Add sample books if database is empty
    if Book.query.count() == 0:
        sample_books = [
            Book(title='Python Programming', author='John Smith', isbn='978-0-123456-01-0',
                 category='Computer Science', publisher='Tech Publications',
                 publication_year=2023, total_copies=3, available_copies=3,
                 location='Shelf A1', price=450.00, keywords='python programming coding computer science algorithms'),
            Book(title='Data Structures and Algorithms', author='Jane Doe', isbn='978-0-123456-02-0',
                 category='Computer Science', publisher='Academic Press',
                 publication_year=2022, total_copies=4, available_copies=4,
                 location='Shelf A2', price=550.00, keywords='data structures algorithms computer science programming'),
            Book(title='Introduction to Machine Learning', author='Robert Chen', isbn='978-0-123456-03-0',
                 category='Computer Science', publisher='ML Publishing',
                 publication_year=2024, total_copies=2, available_copies=2,
                 location='Shelf A3', price=650.00, keywords='machine learning artificial intelligence AI data science'),
            Book(title='Database Management Systems', author='Maria Garcia', isbn='978-0-123456-04-0',
                 category='Computer Science', publisher='DB Press',
                 publication_year=2021, total_copies=3, available_copies=3,
                 location='Shelf A1', price=480.00, keywords='database SQL management systems data storage'),
            Book(title='Web Development with Flask', author='David Wilson', isbn='978-0-123456-05-0',
                 category='Computer Science', publisher='Web Tech Books',
                 publication_year=2023, total_copies=2, available_copies=2,
                 location='Shelf A4', price=399.00, keywords='web development flask python backend API'),
            Book(title='Operating Systems Concepts', author='Thomas Anderson', isbn='978-0-123456-06-0',
                 category='Computer Science', publisher='OS Publications',
                 publication_year=2022, total_copies=3, available_copies=3,
                 location='Shelf A5', price=520.00, keywords='operating systems OS kernel processes threads'),
            Book(title='Digital Signal Processing', author='Sarah Johnson', isbn='978-0-234567-01-0',
                 category='Electronics', publisher='Signal Books',
                 publication_year=2023, total_copies=2, available_copies=2,
                 location='Shelf B1', price=480.00, keywords='signal processing digital electronics DSP filters'),
            Book(title='Microprocessor Systems', author='James Brown', isbn='978-0-234567-02-0',
                 category='Electronics', publisher='Micro Press',
                 publication_year=2022, total_copies=3, available_copies=3,
                 location='Shelf B2', price=420.00, keywords='microprocessor embedded systems CPU architecture'),
            Book(title='VLSI Design', author='Emily Davis', isbn='978-0-234567-03-0',
                 category='Electronics', publisher='VLSI Publications',
                 publication_year=2024, total_copies=2, available_copies=2,
                 location='Shelf B3', price=550.00, keywords='VLSI design semiconductor chips integrated circuits'),
            Book(title='Communication Systems', author='Michael Lee', isbn='978-0-234567-04-0',
                 category='Electronics', publisher='Comm Books',
                 publication_year=2021, total_copies=3, available_copies=3,
                 location='Shelf B1', price=460.00, keywords='communication systems wireless signal modulation'),
            Book(title='Organic Chemistry', author='Lisa Wang', isbn='978-0-345678-01-0',
                 category='Chemistry', publisher='Chem Publications',
                 publication_year=2023, total_copies=4, available_copies=4,
                 location='Shelf C1', price=380.00, keywords='organic chemistry compounds reactions synthesis'),
            Book(title='Physical Chemistry', author='Daniel Kim', isbn='978-0-345678-02-0',
                 category='Chemistry', publisher='PhysChem Press',
                 publication_year=2022, total_copies=3, available_copies=3,
                 location='Shelf C2', price=420.00, keywords='physical chemistry thermodynamics kinetics equilibrium'),
            Book(title='Analytical Chemistry', author='Rachel Green', isbn='978-0-345678-03-0',
                 category='Chemistry', publisher='Analytical Books',
                 publication_year=2024, total_copies=2, available_copies=2,
                 location='Shelf C1', price=350.00, keywords='analytical chemistry spectroscopy chromatography'),
            Book(title='Physics for Engineers', author='Kevin White', isbn='978-0-456789-01-0',
                 category='Physics', publisher='Engineering Physics',
                 publication_year=2023, total_copies=3, available_copies=3,
                 location='Shelf D1', price=450.00, keywords='physics engineering mechanics thermodynamics optics'),
            Book(title='Advanced Mathematics', author='Nancy Taylor', isbn='978-0-567890-01-0',
                 category='Mathematics', publisher='Math Press',
                 publication_year=2022, total_copies=4, available_copies=4,
                 location='Shelf E1', price=400.00, keywords='mathematics calculus algebra statistics probability'),
            Book(title='English Literature', author='William Clark', isbn='978-0-678901-01-0',
                 category='Literature', publisher='Lit Publications',
                 publication_year=2021, total_copies=3, available_copies=3,
                 location='Shelf F1', price=320.00, keywords='literature english writing prose poetry drama'),
            Book(title='Introduction to Psychology', author='Amanda Martinez', isbn='978-0-789012-01-0',
                 category='Psychology', publisher='Psych Books',
                 publication_year=2023, total_copies=2, available_copies=2,
                 location='Shelf G1', price=380.00, keywords='psychology behavior cognitive science mental health'),
            Book(title='Economics Fundamentals', author='Christopher Hall', isbn='978-0-890123-01-0',
                 category='Economics', publisher='Econ Press',
                 publication_year=2022, total_copies=3, available_copies=3,
                 location='Shelf H1', price=420.00, keywords='economics microeconomics macroeconomics market trade'),
            Book(title='Environmental Science', author='Jennifer Adams', isbn='978-0-901234-01-0',
                 category='Science', publisher='Eco Publications',
                 publication_year=2024, total_copies=2, available_copies=2,
                 location='Shelf I1', price=350.00, keywords='environment ecology sustainability climate pollution'),
            Book(title='Business Management', author='Richard Thompson', isbn='978-1-012345-01-0',
                 category='Management', publisher='Biz Books',
                 publication_year=2023, total_copies=3, available_copies=3,
                 location='Shelf J1', price=450.00, keywords='management business leadership strategy operations')
        ]
        
        for book in sample_books:
            db.session.add(book)
        db.session.commit()
        print(f"Added {len(sample_books)} sample books to the catalog.")
    
    # Add sample members if database is empty
    if Member.query.count() == 0:
        sample_members = [
            Member(name='Rahul Sharma', member_id='STU001', email='rahul@college.edu',
                   membership_type='student', department='Computer Science'),
            Member(name='Priya Patel', member_id='STU002', email='priya@college.edu',
                   membership_type='student', department='Electronics'),
            Member(name='Amit Kumar', member_id='STU003', email='amit@college.edu',
                   membership_type='student', department='Chemistry'),
            Member(name='Sneha Reddy', member_id='STU004', email='sneha@college.edu',
                   membership_type='student', department='Physics'),
            Member(name='Vikram Singh', member_id='FAC001', email='vikram@college.edu',
                   membership_type='faculty', department='Computer Science'),
            Member(name='Anita Desai', member_id='FAC002', email='anita@college.edu',
                   membership_type='faculty', department='Mathematics'),
            Member(name='Manoj Gupta', member_id='STU005', email='manoj@college.edu',
                   membership_type='student', department='Electronics'),
            Member(name='Kavita Nair', member_id='STU006', email='kavita@college.edu',
                   membership_type='student', department='Literature')
        ]
        
        for member in sample_members:
            db.session.add(member)
        db.session.commit()
        print(f"Added {len(sample_members)} sample members.")


if __name__ == '__main__':
    with app.app_context():
        init_db()
    print("Library Management System starting...")
    print("Search endpoint: /search?q=<query>")
    print("Admin dashboard: /admin/dashboard")
    app.run(debug=True, port=5000)
