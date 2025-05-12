import psycopg2
import io
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import csv



class PostgresBulkInserter:
    def __init__(self, db_host, db_port, db_name, db_user, db_password):
        """
        Initialize the bulk inserter with PostgreSQL connection parameters.
        """
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
    
    def dicts_to_csv(self, data, header=None):
        """
        Convert a list of dictionaries to CSV format using StringIO and csv.DictWriter.
        This method ensures proper quoting to handle fields containing commas, quotes, or newlines.

        Args:
            data (list): List of dictionaries. If header is None, keys from the first dict are used.
            header (str or list, optional): Comma-separated string or list for CSV header.
            
        Returns:
            StringIO: An in-memory CSV file-like object.
        """
        output = io.StringIO()
        if not data:
            return output
        
        # Determine header keys
        if header is None:
            header_keys = list(data[0].keys())
        else:
            if isinstance(header, str):
                header_keys = [h.strip() for h in header.split(",")]
            else:
                header_keys = header
        
        # Use csv.DictWriter with quoting to handle fields properly
        writer = csv.DictWriter(output, fieldnames=header_keys, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        
        for row in data:
            # for k, v in row.items():
            #     if v in (None, "", "NULL"):
            #         row[k] = ""
            writer.writerow(row)
        
        output.seek(0)
        return output

    def bulk_insert(self, table, data, header=None):
        """
        Bulk insert data into the specified table using PostgreSQL COPY command.
        
        Args:
            table (str): Name of the target table.
            data (list): List of dictionaries to insert.
            header (str or list, optional): Optional header defining column order.
                                             If not provided, keys from the first dictionary are used.
        """
        if not data:
            print("No data to insert.")
            return

        # Convert dictionary data to CSV using our improved method.
        csv_data = self.dicts_to_csv(data, header=header)
        
        # Determine column names for the COPY command
        if header is None:
            header_keys = list(data[0].keys())
        else:
            if isinstance(header, str):
                header_keys = [h.strip() for h in header.split(",")]
            else:
                header_keys = header
        columns = ", ".join(header_keys)

        # Connect to PostgreSQL and perform the COPY command
        conn = psycopg2.connect(
            host=self.db_host,
            port=self.db_port,
            dbname=self.db_name,
            user=self.db_user,
            password=self.db_password
        )
        cur = conn.cursor()
        copy_sql = f"COPY {table} ({columns}) FROM STDIN WITH CSV HEADER NULL ''"
        cur.copy_expert(sql=copy_sql, file=csv_data)
        conn.commit()
        cur.close()
        conn.close()


# Example usage:
if __name__ == "__main__":
    import random

    # Initialize the inserter with your PostgreSQL connection details
    inserter = PostgresBulkInserter(
        db_host="localhost",
        db_port="5432",
        db_name="mydatabase",
        db_user="postgres",
        db_password="password"
    )

    # Generate 1,000,000 dictionary records with arbitrary keys
    data = [
        {
            "name": f"User{i}", 
            "email": f"user{i}@example.com", 
            "age": random.randint(18, 60)
        }
        for i in range(1000000)
    ]

    # Perform the bulk insert into the "users" table.
    # The table must have columns that correspond to the keys in the dictionaries.
    inserter.bulk_insert("users", data)
