import sys
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
                             QVBoxLayout, QWidget, QPushButton, QLabel, QHBoxLayout, QTabWidget)
from PyQt5.QtCore import QDateTime

#CSVtest
import csv
from PyQt5.QtWidgets import QFileDialog

from PyQt5.QtWidgets import QProgressDialog, QMessageBox
from PyQt5.QtCore import Qt

# Replace with your own WooCommerce credentials and domain
url = 'https://olsenbatterier.com/wp-json/wc/v3'
consumer_key = 'ck_dfea398c9f4189db190e4303c8d20b00ed7c7648'
consumer_secret = 'cs_6bcb8353f912f037803f2604d4ff3f84ab791c02'

# Fetch orders from WooCommerce REST API
def fetch_orders():
    response = requests.get(f"{url}/orders", auth=(consumer_key, consumer_secret))

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error fetching orders: {response.status_code} - {response.text}")

# Populate the table with order data
def populate_table():
    orders = fetch_orders()
    table.setRowCount(len(orders))

    for i, order in enumerate(orders):
        table.setItem(i, 0, QTableWidgetItem(str(order['id'])))
        table.setItem(i, 1, QTableWidgetItem(order['status']))
        table.setItem(i, 2, QTableWidgetItem(order['total']))
        table.setItem(i, 3, QTableWidgetItem(order['date_created']))

    updated_time.setText(f"Sist oppdatert: {QDateTime.currentDateTime().toString()}")

# Create a simple desktop app with PyQt5
app = QApplication(sys.argv)

# Create main window
window = QMainWindow()
window.setWindowTitle('Olsen Batterier Ordrer')
window.setGeometry(100, 100, 800, 600)

# Create a central widget for the main window
central_widget = QWidget()
window.setCentralWidget(central_widget)

# Create a vertical layout for the central widget
layout = QVBoxLayout()
central_widget.setLayout(layout)

# Create QTabWidget for navigation
tab_widget = QTabWidget()
layout.addWidget(tab_widget)

# Create tabs
tab1 = QWidget()
tab2 = QWidget()
tab3 = QWidget()

# Add tabs to the QTabWidget
tab_widget.addTab(tab1, "Tab 1")
tab_widget.addTab(tab2, "Tab 2")
tab_widget.addTab(tab3, "Tab 3")

# Set up layouts for the tabs
tab1_layout = QVBoxLayout()
tab1.setLayout(tab1_layout)

tab2_layout = QVBoxLayout()
tab2.setLayout(tab2_layout)

tab3_layout = QVBoxLayout()
tab3.setLayout(tab3_layout)

# Create a QHBoxLayout for the Refresh button and the last updated time label
top_layout = QHBoxLayout()
tab1_layout.addLayout(top_layout)

# Create a Refresh button
refresh_button = QPushButton('Oppdater')
refresh_button.clicked.connect(populate_table)
top_layout.addWidget(refresh_button)

# Create a QLabel widget for the last updated time
updated_time = QLabel()
top_layout.addWidget(updated_time)

# Create a table widget to display orders
table = QTableWidget()
tab1_layout.addWidget(table)

# Set table headers
table.setColumnCount(4)
table.setHorizontalHeaderLabels(['Order ID', 'Status', 'Total', 'Date'])

# Tab 2 content
tab2_label = QLabel("This is the content of Tab 2")
tab2_layout.addWidget(tab2_label)

# Tab 3 content
tab3_label = QLabel("This is the content of Tab 3")
tab3_layout.addWidget(tab3_label)

# Function to open a file dialog and select a CSV file
def open_csv_file():
    file_name, _ = QFileDialog.getOpenFileName(window, 'Open CSV File', '', 'CSV Files (*.csv);;All Files (*)')
    if file_name:
        try:
            update_stock_from_csv(file_name)
        except Exception as e:
            print(f"An error occurred while processing the CSV file: {e}")


# Function to update stock levels from a CSV file
def update_stock_from_csv(file_name):
    updated_count = 0
    skipped_count = 0
    skipped_messages = []

    with open(file_name, 'r') as file:
        csv_reader = csv.DictReader(file)
        total_rows = sum(1 for row in csv_reader)
        file.seek(0)
        csv_reader = csv.DictReader(file)

        progress_dialog = QProgressDialog("Updating stock...", "Cancel", 0, total_rows, window)
        progress_dialog.setWindowTitle("Updating")
        progress_dialog.setWindowModality(Qt.WindowModal)

        for i, row in enumerate(csv_reader):
            QApplication.processEvents()
            sku = row['sku']
            stock = int(row['stock'])
            success, message = update_stock_by_sku(sku, stock)

            if success:
                updated_count += 1
            else:
                skipped_count += 1
                skipped_messages.append(message)

            progress_dialog.setValue(i + 1)
            if progress_dialog.wasCanceled():
                break

        progress_dialog.setValue(total_rows)

    results_message = f"{updated_count}/{total_rows} products updated, {skipped_count} skipped."
    if skipped_messages:
        results_message += "\n\nSkipped products:\n" + "\n".join(skipped_messages)

    QMessageBox.information(window, "Update Complete", results_message)


# Function to update the stock level of a product by SKU using the WooCommerce API
def update_stock_by_sku(sku, stock):
    success = False
    message = ""

    response = requests.get(f"{url}/products", params={'sku': sku}, auth=(consumer_key, consumer_secret))
    if response.status_code == 200:
        product_data = response.json()
        if product_data:
            product_id = product_data[0]['id']
            update_data = {'stock_quantity': stock}
            response = requests.put(f"{url}/products/{product_id}", json=update_data, auth=(consumer_key, consumer_secret))
            if response.status_code == 200:
                success = True
                message = f"Updated stock for product {sku}"
            else:
                message = f"Error updating stock for product {sku}: {response.status_code} - {response.text}"
        else:
            message = f"Product with SKU {sku} not found."
    else:
        message = f"Error fetching product by SKU {sku}: {response.status_code} - {response.text}"

    return success, message

# Add a button to open the CSV file

import_csv_button = QPushButton('Import Stock from CSV')
import_csv_button.clicked.connect(open_csv_file)
top_layout.addWidget(import_csv_button)

# Populate the table with initial order data
populate_table()

# Show the main window and start the app
window.show()
sys.exit(app.exec_())
