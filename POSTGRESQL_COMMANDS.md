# PostgreSQL Database Commands for LexSaksham

## 🔹 **1. Basic Connection Commands**

### **Connect to PostgreSQL Database**
```bash
# Connect to default database
psql -U postgres

# Connect to specific database
psql -U postgres -d your_database_name

# Connect with host and port
psql -h localhost -p 5432 -U postgres -d your_database_name

# Connect with password prompt
psql -U postgres -W
```

### **If PostgreSQL is not in PATH (Windows)**
```bash
# Navigate to PostgreSQL bin directory first
cd "C:\Program Files\PostgreSQL\<version>\bin"

# Then run psql
psql -U postgres
```

---

## 🔹 **2. Database Information Commands**

### **List All Databases**
```sql
\l
-- or
\list
```

### **Connect to a Database**
```sql
\c database_name
-- or
\connect database_name
```

### **Show Current Database**
```sql
SELECT current_database();
```

### **Show Current User**
```sql
SELECT current_user;
```

### **Show Database Size**
```sql
SELECT pg_size_pretty(pg_database_size('database_name'));
```

---

## 🔹 **3. Table Commands**

### **List All Tables in Current Database**
```sql
\dt
-- or
\dt+
-- (+ shows additional info like size)
```

### **List All Tables in All Schemas**
```sql
\dt *.*
```

### **Describe Table Structure**
```sql
\d table_name
-- or
\d+ table_name
-- (+ shows additional details)
```

### **List All Columns in a Table**
```sql
\d+ table_name
```

### **Show Table Size**
```sql
SELECT pg_size_pretty(pg_total_relation_size('table_name'));
```

---

## 🔹 **4. Data Query Commands**

### **Count Rows in a Table**
```sql
SELECT COUNT(*) FROM table_name;
```

### **View All Data in a Table**
```sql
SELECT * FROM table_name;
```

### **View Limited Rows**
```sql
SELECT * FROM table_name LIMIT 10;
```

### **View Specific Columns**
```sql
SELECT column1, column2 FROM table_name;
```

### **Search for Specific Data**
```sql
SELECT * FROM table_name WHERE column_name = 'value';
```

---

## 🔹 **5. Schema and Structure Commands**

### **List All Schemas**
```sql
\dn
```

### **Show Table Indexes**
```sql
\di table_name
```

### **Show Table Constraints**
```sql
\d+ table_name
```

### **List All Sequences**
```sql
\ds
```

### **List All Views**
```sql
\dv
```

---

## 🔹 **6. User and Permission Commands**

### **List All Users/Roles**
```sql
\du
-- or
SELECT * FROM pg_user;
```

### **Show User Permissions**
```sql
\dp table_name
-- or
SELECT * FROM information_schema.table_privileges WHERE table_name = 'table_name';
```

---

## 🔹 **7. Useful Information Queries**

### **Show All Tables with Row Counts**
```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = schemaname AND table_name = tablename) as row_count
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### **Show Database Connections**
```sql
SELECT * FROM pg_stat_activity;
```

### **Show Database Version**
```sql
SELECT version();
```

### **Show PostgreSQL Configuration**
```sql
SHOW ALL;
```

---

## 🔹 **8. Common Operations**

### **Create a New Database**
```sql
CREATE DATABASE database_name;
```

### **Drop a Database**
```sql
DROP DATABASE database_name;
```

### **Backup Database (from command line, not psql)**
```bash
pg_dump -U postgres -d database_name > backup.sql
```

### **Restore Database (from command line)**
```bash
psql -U postgres -d database_name < backup.sql
```

---

## 🔹 **9. Exit Commands**

### **Exit psql**
```sql
\q
-- or
exit
```

---

## 🔹 **10. Quick Check Commands for LexSaksham**

### **Check if LexSaksham tables exist**
```sql
-- List all tables
\dt

-- Check for common table names
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE '%contract%' OR table_name LIKE '%clause%' OR table_name LIKE '%judgment%';
```

### **Check table structure (if tables exist)**
```sql
-- Example: Check contracts table
\d contracts

-- Example: Check clauses table
\d clauses

-- Example: Check judgments table
\d judgments
```

### **View sample data**
```sql
-- View first 5 contracts
SELECT * FROM contracts LIMIT 5;

-- View first 5 clauses
SELECT * FROM clauses LIMIT 5;

-- View first 5 judgments
SELECT * FROM judgments LIMIT 5;
```

---

## 🔹 **11. Troubleshooting Commands**

### **Check if PostgreSQL is running**
```bash
# Windows
sc query postgresql-x64-<version>

# Or check service status
services.msc
# Then look for PostgreSQL service
```

### **Check PostgreSQL port**
```sql
SHOW port;
```

### **Check PostgreSQL data directory**
```sql
SHOW data_directory;
```

### **Check connection limit**
```sql
SHOW max_connections;
```

---

## 🔹 **12. Windows-Specific Commands**

### **Start PostgreSQL Service**
```bash
net start postgresql-x64-<version>
```

### **Stop PostgreSQL Service**
```bash
net stop postgresql-x64-<version>
```

### **Find PostgreSQL Installation**
```bash
# Common locations:
# C:\Program Files\PostgreSQL\<version>\bin\psql.exe
# C:\Program Files (x86)\PostgreSQL\<version>\bin\psql.exe
```

---

## 🔹 **13. Quick Reference**

| Command | Description |
|---------|-------------|
| `\l` | List all databases |
| `\c dbname` | Connect to database |
| `\dt` | List all tables |
| `\d table_name` | Describe table structure |
| `\du` | List all users |
| `\q` | Quit psql |
| `\?` | Show help for psql commands |
| `\h` | Show help for SQL commands |
| `\timing` | Toggle query timing |
| `\x` | Toggle expanded display |

---

## 🔹 **14. Example Workflow**

```bash
# 1. Connect to PostgreSQL
psql -U postgres

# 2. List databases
\l

# 3. Connect to your database
\c lexsaksham_db

# 4. List tables
\dt

# 5. Check table structure
\d contracts

# 6. View data
SELECT * FROM contracts LIMIT 10;

# 7. Exit
\q
```

---

## 🔹 **15. Environment Variables (if needed)**

If you need to set connection details:
```bash
# Windows PowerShell
$env:PGHOST="localhost"
$env:PGPORT="5432"
$env:PGUSER="postgres"
$env:PGPASSWORD="your_password"
$env:PGDATABASE="your_database"

# Then connect
psql
```

---

## 🔹 **16. Check Database Connection from Python**

If you want to test connection from Python:
```python
import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="your_database",
        user="postgres",
        password="your_password"
    )
    print("✅ Connected successfully!")
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    print(cursor.fetchone())
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

---

## **Note:**
- Replace `postgres` with your actual PostgreSQL username
- Replace `your_database_name` with your actual database name
- Default port is usually `5432`
- Default superuser is usually `postgres`


