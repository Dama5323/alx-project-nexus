from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError
import time

class Command(BaseCommand):
    help = 'Resets all database connections and verifies connectivity'

    def handle(self, *args, **options):
        self.stdout.write("Resetting database connections...")
        
        # Close all connections
        for conn_name in connections:
            try:
                connections[conn_name].close()
                self.stdout.write(f"Closed connection: {conn_name}")
            except OperationalError as e:
                self.stdout.write(self.style.ERROR(
                    f"Error closing {conn_name}: {str(e)}"
                ))

        # Test connections
        self.stdout.write("\nTesting database connections:")
        for conn_name in connections:
            try:
                with connections[conn_name].cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    self.stdout.write(self.style.SUCCESS(
                        f"{conn_name}: Connection successful (result: {result})"
                    ))
            except OperationalError as e:
                self.stdout.write(self.style.ERROR(
                    f"{conn_name}: Connection failed - {str(e)}"
                ))

        self.stdout.write(self.style.SUCCESS(
            "\nDatabase connection reset complete"
        ))