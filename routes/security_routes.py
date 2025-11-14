import csv
import os
from flask import Blueprint, render_template, jsonify, current_app
from utils.security import admin_required, VillainSecurity

security_bp = Blueprint(
    'security',
    __name__,
    url_prefix='/security'
)


def _read_csv_rows(file_path, fallback_rows):
    """Load CSV rows into dictionaries or return fallback."""
    if not file_path:
        return fallback_rows

    if os.path.exists(file_path):
        try:
            with open(file_path, newline='', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file)
                rows = [row for row in reader]
                if rows:
                    return rows
        except Exception as exc:
            print(f"Failed to read {file_path}: {exc}")

    return fallback_rows


def _default_classification_rows():
    return [
        {
            'Data Asset': 'User Profiles',
            'Description': 'Name, email, phone, delivery addresses',
            'Classification': 'Confidential',
            'Storage': 'MySQL - users table, encrypted backups',
            'Access Roles': 'customer, admin'
        },
        {
            'Data Asset': 'Payment Tokens',
            'Description': 'Third-party payment references',
            'Classification': 'Restricted',
            'Storage': 'Secure payment gateway, hashed references only',
            'Access Roles': 'admin'
        },
        {
            'Data Asset': 'Restaurant Menus',
            'Description': 'Menu items, pricing, availability',
            'Classification': 'Public',
            'Storage': 'MySQL - menu_items table, CDN cache',
            'Access Roles': 'customer, restaurant, admin'
        },
        {
            'Data Asset': 'Order Ledger',
            'Description': 'Order totals, status, blockchain hash',
            'Classification': 'Private',
            'Storage': 'MySQL orders table + blockchain_records',
            'Access Roles': 'restaurant, admin'
        }
    ]


def _default_gdpr_controls():
    return [
        {'Control': 'Right to Access', 'Evidence': 'GDPR data portal', 'Status': 'Compliant'},
        {'Control': 'Right to Portability', 'Evidence': 'JSON export endpoint', 'Status': 'Compliant'},
        {'Control': 'Right to Erasure', 'Evidence': 'Anonymise + delete workflow', 'Status': 'Compliant'},
        {'Control': 'Consent Management', 'Evidence': 'Privacy toggles in portal', 'Status': 'Partially compliant'},
    ]


@security_bp.route('/configuration')
@admin_required
def security_configuration():
    """Render security config dashboard from CSV-driven controls."""
    classification_path = current_app.config.get('DATA_CLASSIFICATION_PATH')
    gdpr_path = current_app.config.get('GDPR_COMPLIANCE_PATH')

    classification_rows = _read_csv_rows(classification_path, _default_classification_rows())
    gdpr_rows = _read_csv_rows(gdpr_path, _default_gdpr_controls())

    return render_template(
        'admin/security_config.html',
        security_domain=current_app.config.get('SECURITY_DOMAIN'),
        data_classification=classification_rows,
        gdpr_controls=gdpr_rows,
        access_matrix=VillainSecurity.ROLE_PERMISSIONS
    )


@security_bp.route('/classification.json')
@admin_required
def classification_json():
    """Expose classification spreadsheet as JSON for reporting."""
    classification_rows = _read_csv_rows(
        current_app.config.get('DATA_CLASSIFICATION_PATH'),
        _default_classification_rows()
    )
    return jsonify({
        'count': len(classification_rows),
        'items': classification_rows
    })


@security_bp.route('/gdpr.json')
@admin_required
def gdpr_json():
    """Expose GDPR compliance spreadsheet as JSON for reporting."""
    gdpr_rows = _read_csv_rows(
        current_app.config.get('GDPR_COMPLIANCE_PATH'),
        _default_gdpr_controls()
    )
    return jsonify({
        'count': len(gdpr_rows),
        'items': gdpr_rows
    })

