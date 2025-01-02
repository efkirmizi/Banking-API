import pymysql.cursors

# MySQL database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',       # Replace with your MySQL username
    'password': 'password',   # Replace with your MySQL password
    'database': 'bank',   # Replace with your database name
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

def init_db():
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute('''
        CREATE TABLE user (
            user_id CHAR(36) PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL,
            role ENUM('ADMIN', 'USER') NOT NULL DEFAULT 'USER',
            customer_id CHAR(36),
            FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON UPDATE CASCADE ON DELETE RESTRICT
        );

        CREATE TABLE customer (
            customer_id CHAR(36) PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            date_of_birth DATE NOT NULL,
            phone_number VARCHAR(15) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            address_line1 VARCHAR(255) NOT NULL,
            address_line2 VARCHAR(255),
            city VARCHAR(100) NOT NULL,
            zip_code VARCHAR(20) NOT NULL,
            wage_declaration DECIMAL(15, 2) DEFAULT 0
        );

        CREATE TABLE branch (
            branch_id CHAR(36) PRIMARY KEY,
            branch_name VARCHAR(100) UNIQUE NOT NULL,
            address_line1 VARCHAR(100) NOT NULL,
            address_line2 VARCHAR(100),
            city VARCHAR(100) NOT NULL,
            zip_code VARCHAR(20) NOT NULL,
            phone_number VARCHAR(15) UNIQUE NOT NULL
        );

        CREATE TABLE account (
            account_id CHAR(36) PRIMARY KEY,
            customer_id CHAR(36) NOT NULL,
            account_type ENUM('CHECKING', 'SAVINGS') NOT NULL,
            balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
            creation_date DATETIME NOT NULL,
            branch_id CHAR(36) NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON UPDATE CASCADE ON DELETE RESTRICT,
            FOREIGN KEY (branch_id) REFERENCES branch(branch_id) ON UPDATE CASCADE ON DELETE RESTRICT,
            CONSTRAINT check_balance_positive CHECK (balance >= 0)
        );

        CREATE TABLE loan (
            loan_id CHAR(36) PRIMARY KEY,
            customer_id CHAR(36) NOT NULL,
            loan_type ENUM('HOME', 'AUTO', 'PERSONAL') NOT NULL,
            principal_amount DECIMAL(15, 2) NOT NULL,
            interest_rate DECIMAL(5, 2) NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            status ENUM('ACTIVE', 'PAID_OFF', 'DEFAULT') NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON UPDATE CASCADE ON DELETE RESTRICT,
            CONSTRAINT check_principal_positive CHECK (principal_amount > 0),
            CONSTRAINT check_interest_non_negative CHECK (interest_rate >= 0),
            CONSTRAINT check_dates_valid CHECK (start_date < end_date)
        );

        CREATE TABLE loan_payment (
            loan_payment_id CHAR(36) PRIMARY KEY,
            loan_id CHAR(36) NOT NULL,
            payment_date DATETIME NOT NULL,
            payment_amount DECIMAL(15, 2) NOT NULL,
            remaining_balance DECIMAL(15, 2),
            FOREIGN KEY (loan_id) REFERENCES loan(loan_id) ON UPDATE CASCADE ON DELETE RESTRICT,
            CONSTRAINT check_payment_positive CHECK (payment_amount > 0),
            CONSTRAINT check_remaining_non_negative CHECK (remaining_balance >= 0)
        );

        CREATE TABLE employee (
            employee_id CHAR(36) PRIMARY KEY,
            branch_id CHAR(36) NOT NULL,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            position VARCHAR(100) NOT NULL,
            hire_date DATETIME NOT NULL,
            phone_number VARCHAR(15) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            FOREIGN KEY (branch_id) REFERENCES branch(branch_id) ON UPDATE CASCADE ON DELETE RESTRICT
        );

        CREATE TABLE card (
            card_id CHAR(36) PRIMARY KEY,
            account_id CHAR(36) NOT NULL,
            card_type ENUM('DEBIT', 'CREDIT') NOT NULL,
            card_number VARCHAR(16) UNIQUE NOT NULL,
            expiration_date DATE NOT NULL,
            cvv VARCHAR(3) NOT NULL,
            status ENUM('ACTIVE', 'BLOCKED', 'EXPIRED') NOT NULL,
            FOREIGN KEY (account_id) REFERENCES account(account_id) ON UPDATE CASCADE ON DELETE RESTRICT
        );

        CREATE TABLE transaction (
            transaction_id CHAR(36) PRIMARY KEY,
            from_account_id CHAR(36) NOT NULL,
            to_account_id CHAR(36),
            transaction_type ENUM('DEPOSIT', 'WITHDRAWAL', 'TRANSFER') NOT NULL,
            amount DECIMAL(15, 2) NOT NULL,
            transaction_timestamp DATETIME NOT NULL,
            FOREIGN KEY (from_account_id) REFERENCES account(account_id) ON UPDATE CASCADE ON DELETE RESTRICT,
            FOREIGN KEY (to_account_id) REFERENCES account(account_id) ON UPDATE CASCADE ON DELETE SET NULL,
            CONSTRAINT check_amount_positive CHECK (amount > 0)
        );

        CREATE TABLE customer_support (
            ticket_id CHAR(36) PRIMARY KEY,
            customer_id CHAR(36) NOT NULL,
            employee_id CHAR(36) NOT NULL,
            issue_description TEXT NOT NULL,
            status ENUM('OPEN', 'IN_PROGRESS', 'RESOLVED') NOT NULL,
            created_date DATETIME NOT NULL,
            resolved_date DATETIME,
            FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON UPDATE CASCADE ON DELETE RESTRICT,
            FOREIGN KEY (employee_id) REFERENCES employee(employee_id) ON UPDATE CASCADE ON DELETE RESTRICT
        );

        CREATE TABLE credit_score (
            credit_score_id CHAR(36) PRIMARY KEY,
            customer_id CHAR(36) NOT NULL,
            score DECIMAL(5, 2) NOT NULL,
            risk_category VARCHAR(50) NOT NULL,
            computed_by_system BOOLEAN,
            FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON UPDATE CASCADE ON DELETE RESTRICT
        );
        ''')
    connection.commit()
    connection.close()
