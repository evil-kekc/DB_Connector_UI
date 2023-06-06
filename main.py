import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QLabel, QLineEdit, QPushButton, QMessageBox,
    QTableWidget, QTableWidgetItem, QFormLayout,
    QHBoxLayout, QDialog, QDialogButtonBox
)

import psycopg2


class DatabaseConnection:
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def connect(self):
        try:
            connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password
            )
            return connection
        except psycopg2.Error as e:
            QMessageBox.critical(
                None,
                "Ошибка",
                f"Не удалось подключиться к базе данных:\n\n{str(e)}"
            )
            return None


class AddRecordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить запись")

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.age_edit = QLineEdit()

        form_layout.addRow("Name:", self.name_edit)
        form_layout.addRow("Age:", self.age_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addLayout(form_layout)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_record_data(self):
        name = self.name_edit.text()
        age = self.age_edit.text()
        return (name, age)


class DatabaseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Database App")

        self.connection = None

        main_layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.host_edit = QLineEdit()
        self.port_edit = QLineEdit()
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)

        connect_button = QPushButton("Подключиться")
        connect_button.clicked.connect(self.connect_to_database)

        main_layout.addWidget(QLabel("Host:"))
        main_layout.addWidget(self.host_edit)
        main_layout.addWidget(QLabel("Port:"))
        main_layout.addWidget(self.port_edit)
        main_layout.addWidget(QLabel("Логин:"))
        main_layout.addWidget(self.username_edit)
        main_layout.addWidget(QLabel("Пароль:"))
        main_layout.addWidget(self.password_edit)
        main_layout.addWidget(connect_button)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(["ID", "Name", "Age"])
        main_layout.addWidget(self.table_widget)

        add_button = QPushButton("Добавить запись")
        add_button.clicked.connect(self.add_record)
        delete_button = QPushButton("Удалить запись")
        delete_button.clicked.connect(self.delete_record)
        edit_button = QPushButton("Изменить запись")
        edit_button.clicked.connect(self.edit_record)
        filter_button = QPushButton("Фильтр")
        filter_button.clicked.connect(self.filter_records)
        report_button = QPushButton("Создать отчет")
        report_button.clicked.connect(self.generate_report)

        button_layout = QHBoxLayout()
        button_layout.addWidget(add_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(filter_button)
        button_layout.addWidget(report_button)
        main_layout.addLayout(button_layout)

    def connect_to_database(self):
        host = self.host_edit.text()
        port = self.port_edit.text()
        username = self.username_edit.text()
        password = self.password_edit.text()

        self.connection = DatabaseConnection(host, port, username, password).connect()
        if self.connection:
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS records (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255),
                    age INTEGER
                )
            """)
            self.connection.commit()
            cursor.close()
            QMessageBox.information(
                None,
                "Ок",
                "Успешное подключение к базе данных."
            )
            self.load_records()

    def add_record(self):
        if not self.connection:
            QMessageBox.warning(
                None,
                "Ошибка",
                "Сначала необходимо подключиться к базе данных."
            )
            return

        dialog = AddRecordDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            name, age = dialog.get_record_data()
            cursor = self.connection.cursor()
            cursor.execute("INSERT INTO records (name, age) VALUES (%s, %s)", (name, age))
            self.connection.commit()
            cursor.close()
            self.load_records()

    def delete_record(self):
        if not self.connection:
            QMessageBox.warning(
                None,
                "Ошибка",
                "Сначала необходимо подключиться к базе данных."
            )
            return

        selected_row = self.table_widget.currentRow()
        if selected_row >= 0:
            record_id = self.table_widget.item(selected_row, 0).text()
            confirmation = QMessageBox.question(
                None,
                "Confirmation",
                f"Вы уверены, что хотите удалить запись с идентификатором {record_id}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirmation == QMessageBox.Yes:
                cursor = self.connection.cursor()
                cursor.execute("DELETE FROM records WHERE id = %s", (record_id,))
                self.connection.commit()
                cursor.close()
                self.load_records()

    def edit_record(self):
        if not self.connection:
            QMessageBox.warning(
                None,
                "Ошибка",
                "Сначала необходимо подключиться к базе данных."
            )
            return

        selected_row = self.table_widget.currentRow()
        if selected_row >= 0:
            record_id = self.table_widget.item(selected_row, 0).text()
            name = self.table_widget.item(selected_row, 1).text()
            age = self.table_widget.item(selected_row, 2).text()

            dialog = AddRecordDialog(self)
            dialog.name_edit.setText(name)
            dialog.age_edit.setText(age)

            if dialog.exec_() == QDialog.Accepted:
                new_name, new_age = dialog.get_record_data()
                cursor = self.connection.cursor()
                cursor.execute(
                    "UPDATE records SET name = %s, age = %s WHERE id = %s",
                    (new_name, new_age, record_id)
                )
                self.connection.commit()
                cursor.close()
                self.load_records()

    def filter_records(self):
        if not self.connection:
            QMessageBox.warning(
                None,
                "Ошибка",
                "Сначала необходимо подключиться к базе данных."
            )
            return

        # TODO: Filtering logic here
        pass

    def generate_report(self):
        if not self.connection:
            QMessageBox.warning(
                None,
                "Ошибка",
                "Сначала необходимо подключиться к базе данных."
            )
            return

        # TODO: Report generation logic here
        pass

    def load_records(self):
        if not self.connection:
            return

        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM records")
        records = cursor.fetchall()
        cursor.close()

        self.table_widget.setRowCount(len(records))
        for row, record in enumerate(records):
            for col, value in enumerate(record):
                item = QTableWidgetItem(str(value))
                self.table_widget.setItem(row, col, item)

    def closeEvent(self, event):
        if self.connection:
            self.connection.close()

        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DatabaseApp()
    window.show()
    sys.exit(app.exec_())
