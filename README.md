# SACCO System Backend

## Overview

This project is a comprehensive backend system for a Savings and Credit Cooperative Organization (SACCO). It provides a complete financial management solution with secure authentication, member management, contribution tracking, loan processing, and extensive administrative controls.

## Tech Stack

- **Framework**: Django 4.2+
- **API**: Django REST Framework
- **Authentication**: JWT (JSON Web Tokens) with OTP (One-Time Password)
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **File Handling**: Django Storage
- **Security**: Django OTP, Password Hashing, Account Lockout Protection

## Features

### Authentication System

- **Secure Invitation-Based Registration**: New members can only join via admin invitation
- **OTP Authentication**: One-time passwords for secure access
- **KYC Verification**: Document upload and manual verification by admins
- **Account Security**: Password reset, account lockout after failed attempts
- **Activity Logging**: Comprehensive logging of all authentication activities

### Member Management

- **Member Profiles**: Complete profile information including contact details and bank information
- **Membership Status**: Active/inactive status, account hold functionality
- **Document Verification**: KYC document upload and verification workflow
- **Automatic Membership Number Generation**: Based on join date and sequence

### Financial Management

#### Share Capital

- **Share Capital Tracking**: Monitor member share capital contributions
- **Payment Terms**: Customizable terms (12/24 months)
- **Completion Percentage**: Track progress towards 100% share capital fulfillment
- **Target Setting**: Configurable share value targets

#### Monthly Contributions

- **Monthly Contribution Records**: Track recurring member contributions
- **Minimum Amount Enforcement**: Set minimum contribution requirements
- **Contribution Reminders**: Automated email reminders for pending contributions
- **Contribution Reports**: Generate monthly, quarterly reports

#### Loans

- **Loan Applications**: Member loan application submission and processing
- **Approval Workflow**: Review, approve, reject applications with reasons
- **Loan Disbursement**: Record loan disbursements with proper accounting
- **Repayment Tracking**: Monitor and record loan repayments
- **Interest Calculation**: Automatic interest calculation on loans
- **Loan Statements**: Generate comprehensive loan statements
- **Payment Schedules**: Create and track loan repayment schedules
- **Payment Reminders**: Send automatic payment reminders for upcoming/overdue payments
- **Eligibility Checking**: Verify member eligibility for loans based on share capital, existing loans

#### Dividends

- **Dividend Distribution**: Distribute dividends from interest income
- **Percentage Calculation**: Automatic calculation based on member shares
- **Distribution Records**: Track all dividend distributions

### Administrative Functions

- **Admin Dashboard**: Comprehensive admin interface
- **Member Management**: Add, edit, verify members
- **Financial Oversight**: Monitor all financial transactions
- **Transaction Management**: Record and track all financial transactions
- **Mass Communication**: Send emails to all members
- **System Settings**: Configure system parameters (interest rates, share values, etc.)
- **Report Generation**: Create financial and member reports

### Transaction Management

- **Transaction Categories**: Share capital, contributions, loans, dividends, expenses, income
- **Transaction Costs**: Track costs associated with transactions
- **Batch Processing**: Process transactions in batches
- **Bank Accounts**: Manage SACCO bank accounts
- **Bank Transactions**: Record and reconcile bank transactions

### Reporting System

- **Financial Statements**: Balance sheets, income statements, cash flow statements
- **Member Statements**: Individual member financial statements
- **Contribution Reports**: Track contribution patterns and totals
- **Loan Reports**: Analyze loan portfolio and performance
- **Audit Logs**: Comprehensive activity tracking for compliance
- **Custom Reports**: Define and save report templates
- **Scheduled Reports**: Set up automatic report generation

## Project Structure

The system is organized into the following Django apps:

1. **authentication**: Handles user authentication, registration, and security
2. **sacco_core**: Core models and functionality for the SACCO system
3. **members**: Member management functionality
4. **contributions**: Handles share capital and monthly contributions
5. **loans**: Loan processing, disbursement, and repayment
6. **transactions**: Transaction recording and processing
7. **reports**: Report generation and management

## API Endpoints

### Authentication

- `/api/auth/invite/`: Invite new members
- `/api/auth/otp-login/`: Login with OTP
- `/api/auth/complete-registration/`: Complete member registration
- `/api/auth/profile/`: User profile management
- `/api/auth/upload-document/`: Upload KYC documents
- `/api/auth/reset-password-request/`: Request password reset
- `/api/auth/verify-otp/`: Verify OTP codes
- `/api/auth/reset-password/`: Reset password
- `/api/auth/admin/reset-user-otp/<uuid:user_id>/`: Admin reset user OTP
- `/api/auth/admin/toggle-user-status/<uuid:user_id>/`: Toggle member status
- `/api/auth/admin/verify-document/<uuid:document_id>/`: Verify member documents
- `/api/auth/admin/send-mass-email/`: Send emails to all members

### Members

- `/api/members/`: Member listing and management
- `/api/members/<uuid:pk>/`: Specific member details
- `/api/members/<uuid:pk>/toggle-active/`: Toggle member active status
- `/api/members/<uuid:pk>/contributions/`: Member contribution history
- `/api/members/<uuid:pk>/share-capital/`: Member share capital payments
- `/api/members/<uuid:pk>/share-summary/`: Member share and contribution summary
- `/api/members/<uuid:pk>/loans/`: Member loans
- `/api/members/<uuid:pk>/dividends/`: Member dividend history
- `/api/members/<uuid:pk>/documents/`: Member uploaded documents
- `/api/members/<uuid:pk>/activity-logs/`: Member activity logs
- `/api/members/<uuid:pk>/set-share-capital-term/`: Set share capital payment term
- `/api/members/dashboard/`: Member dashboard data
- `/api/members/profile/`: Member profile information

### Contributions

- `/api/contributions/monthly/`: Monthly contribution management
- `/api/contributions/monthly/bulk-create/`: Create multiple contributions at once
- `/api/contributions/monthly/missing-contributions/`: List members with missing contributions
- `/api/contributions/monthly/send-reminders/`: Send contribution reminders
- `/api/contributions/monthly/generate-report/`: Generate contribution report
- `/api/contributions/share-capital/`: Share capital management
- `/api/contributions/share-capital/bulk-create/`: Create multiple share capital payments
- `/api/contributions/share-capital/incomplete-share-capital/`: List members with incomplete share capital
- `/api/contributions/recalculate-shares/`: Recalculate share percentages

### Loans

- `/api/loans/applications/`: Loan application management
- `/api/loans/applications/<uuid:pk>/approve/`: Approve loan application
- `/api/loans/applications/<uuid:pk>/reject/`: Reject loan application
- `/api/loans/loans/`: Loan management
- `/api/loans/loans/<uuid:pk>/disburse/`: Disburse approved loan
- `/api/loans/loans/<uuid:pk>/add-repayment/`: Add loan repayment
- `/api/loans/loans/<uuid:pk>/repayment-schedule/`: Get loan repayment schedule
- `/api/loans/loans/<uuid:pk>/generate-statement/`: Generate loan statement
- `/api/loans/loans/due-payments/`: Get loans with due payments
- `/api/loans/loans/send-payment-reminders/`: Send payment reminders
- `/api/loans/eligibility/`: Check loan eligibility

### Transactions

- `/api/transactions/expenses/`: SACCO expense management
- `/api/transactions/income/`: SACCO income management
- `/api/transactions/batches/`: Transaction batch management
- `/api/transactions/batches/<uuid:pk>/process-batch/`: Process transaction batch
- `/api/transactions/bank-accounts/`: Bank account management
- `/api/transactions/bank-accounts/<uuid:pk>/set-as-primary/`: Set primary bank account
- `/api/transactions/bank-transactions/`: Bank transaction management
- `/api/transactions/bank-transactions/<uuid:pk>/reconcile/`: Reconcile bank transaction

### Reports

- `/api/reports/reports/`: Report management
- `/api/reports/financial-statements/`: Financial statement management
- `/api/reports/financial-statements/<uuid:pk>/approve/`: Approve financial statement
- `/api/reports/member-statements/`: Member statement management
- `/api/reports/audit-logs/`: Audit log access
- `/api/reports/backups/`: System backup management
- `/api/reports/backups/create-backup/`: Create system backup
- `/api/reports/saved-reports/`: Saved report template management
- `/api/reports/saved-reports/<uuid:pk>/run-report/`: Run saved report
- `/api/reports/saved-reports/<uuid:pk>/schedule/`: Schedule saved report

## Models

### Authentication Models

- **SaccoUser**: Extended user model with SACCO-specific fields
- **UserDocument**: KYC documents uploaded by users
- **Invitation**: Member invitations with OTP
- **OTPRequest**: OTP for password resets and verification
- **ActivityLog**: User activity tracking

### Core Models

- **SaccoSettings**: Global SACCO configuration settings
- **ShareCapital**: Share capital contributions
- **MonthlyContribution**: Monthly member contributions
- **MemberShareSummary**: Summary of member shares and contributions
- **DividendDistribution**: Dividend distribution records
- **MemberDividend**: Individual member dividend allocations
- **Loan**: Member loans
- **LoanRepayment**: Loan repayment records
- **Transaction**: Financial transactions
- **FinancialSummary**: SACCO financial summaries

### Contributions Models

- **ContributionReminder**: Reminders for monthly contributions
- **ContributionReport**: Reports on contributions
- **MemberContributionSchedule**: Member contribution schedules

### Loans Models

- **LoanApplication**: Loan applications by members
- **LoanGuarantor**: Guarantors for loans
- **RepaymentSchedule**: Loan repayment schedule
- **LoanStatement**: Loan statements for members
- **LoanNotification**: Notifications for loan activities

### Transactions Models

- **SaccoExpense**: SACCO expenses
- **SaccoIncome**: SACCO income
- **TransactionBatch**: Batch processing for transactions
- **BatchItem**: Individual items in transaction batches
- **TransactionLog**: Audit log for transactions
- **BankAccount**: SACCO bank accounts
- **BankTransaction**: Transactions in bank accounts

### Reports Models

- **Report**: General reports
- **FinancialStatement**: Financial statements
- **MemberStatement**: Member financial statements
- **AuditLog**: System audit logs
- **SystemBackup**: System backup records
- **SavedReport**: Saved report templates

## Setup and Installation

### Prerequisites

- Python 3.8+
- pip
- Virtual environment (optional but recommended)

### Installation Steps

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/sacco-system.git
   cd sacco-system
   ```

2. Create and activate a virtual environment
   ```bash
   python -m venv sacco_env
   source sacco_env/bin/activate  # On Windows: sacco_env\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Apply migrations
   ```bash
   python manage.py migrate
   ```

5. Create a superuser
   ```bash
   python manage.py createsuperuser
   ```

6. Run the server
   ```bash
   python manage.py runserver
   ```

### Environment Variables

For production, set the following environment variables:

- `SECRET_KEY`: Django secret key
- `DEBUG`: Set to False in production
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `DATABASE_URL`: Database connection URL
- `EMAIL_HOST`: SMTP server host
- `EMAIL_PORT`: SMTP server port
- `EMAIL_HOST_USER`: SMTP server username
- `EMAIL_HOST_PASSWORD`: SMTP server password
- `DEFAULT_FROM_EMAIL`: Default sender email

## Security Considerations

- All authentication endpoints use JWT for secure token-based authentication
- Passwords are hashed with Django's default password hasher
- Account lockout after multiple failed login attempts
- OTP for sensitive operations
- Activity logging for auditing
- Role-based access control (Admin vs Member)
- XSS protection with Django's template system
- CSRF protection for all non-GET requests

## Development Guidelines

1. Follow PEP 8 style guidelines
2. Write docstrings for all functions and classes
3. Use Django's testing framework for unit tests
4. Use Django's migration system for database changes
5. Use Django REST Framework's serializers for API inputs/outputs

## Future Enhancements

1. SMS notifications for important events
2. Mobile app integration
3. Advanced reporting with data visualization
4. Automated loan approval based on criteria
5. Integration with payment gateways
6. Enhanced dashboard with analytics
7. Multi-language support

## License

[MIT License](LICENSE)

## Contributors

- Nyandieka Mokua - Initial development