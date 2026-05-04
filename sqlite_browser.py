import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
from pathlib import Path

class SQLiteBrowser:
    def __init__(self, root):
        self.root = root
        self.root.title("SQLite3 Database Browser")
        self.root.geometry("1000x700")
        
        self.conn = None
        self.cursor = None
        self.current_db = None
        self.current_table = None
        self.column_filters = {}
        
        self.setup_ui()
    
    def setup_ui(self):
        # Top frame for file operations
        top_frame = ttk.Frame(self.root)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Button(top_frame, text="Open Database", command=self.open_database).pack(side=tk.LEFT, padx=2)
        ttk.Button(top_frame, text="New Database", command=self.new_database).pack(side=tk.LEFT, padx=2)
        ttk.Button(top_frame, text="Close Database", command=self.close_database).pack(side=tk.LEFT, padx=2)
        
        self.db_label = ttk.Label(top_frame, text="No database loaded", foreground="gray")
        self.db_label.pack(side=tk.LEFT, padx=10)
        
        # Main container with paned window
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Tables list
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="Tables:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        # Scrollbar for tables listbox
        scrollbar = ttk.Scrollbar(left_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tables_listbox = tk.Listbox(left_frame, yscrollcommand=scrollbar.set, width=20)
        self.tables_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tables_listbox.bind('<<ListboxSelect>>', self.on_table_select)
        scrollbar.config(command=self.tables_listbox.yview)
        
        # Right panel - Data view
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=3)
        
        # Table info frame
        info_frame = ttk.Frame(right_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.table_info_label = ttk.Label(info_frame, text="Select a table", font=("Arial", 10))
        self.table_info_label.pack(anchor=tk.W)
        
        # Filter frame label
        filter_label = ttk.Label(right_frame, text="Filters:", font=("Arial", 9, "bold"))
        filter_label.pack(anchor=tk.W, padx=5, pady=(5, 2))
        
        # Filter frame with canvas for horizontal scrolling
        filter_container = ttk.Frame(right_frame)
        filter_container.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        filter_canvas = tk.Canvas(filter_container, height=50, bg="white", highlightthickness=0)
        filter_canvas.pack(side=tk.TOP, fill=tk.X)
        
        filter_scrollbar = ttk.Scrollbar(filter_container, orient=tk.HORIZONTAL, command=filter_canvas.xview)
        filter_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        filter_canvas.configure(xscrollcommand=filter_scrollbar.set)
        
        self.filter_frame = ttk.Frame(filter_canvas)
        filter_canvas.create_window((0, 0), window=self.filter_frame, anchor=tk.NW)
        
        def on_filter_frame_configure(event):
            filter_canvas.configure(scrollregion=filter_canvas.bbox("all"))
        
        self.filter_frame.bind("<Configure>", on_filter_frame_configure)
        
        # Treeview for displaying table data
        tree_frame = ttk.Frame(right_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tree_scroll_y = ttk.Scrollbar(tree_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set
        )
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)
        
        # Bottom frame - Query execution
        bottom_frame = ttk.LabelFrame(self.root, text="SQL Query", padding=5)
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.query_text = tk.Text(bottom_frame, height=4, wrap=tk.WORD)
        self.query_text.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        button_frame = ttk.Frame(bottom_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Execute Query", command=self.execute_query).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Clear", command=lambda: self.query_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=2)
    
    def open_database(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("SQLite Database", "*.db *.sqlite *.sqlite3"), ("All Files", "*.*")]
        )
        if filepath:
            self.load_database(filepath)
    
    def new_database(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite Database", "*.db"), ("SQLite3", "*.sqlite3")]
        )
        if filepath:
            try:
                Path(filepath).touch()
                self.load_database(filepath)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create database: {e}")
    
    def load_database(self, filepath):
        try:
            if self.conn:
                self.conn.close()
            
            self.conn = sqlite3.connect(filepath)
            self.cursor = self.conn.cursor()
            self.current_db = filepath
            
            self.db_label.config(text=f"Database: {Path(filepath).name}", foreground="green")
            self.refresh_tables()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open database: {e}")
    
    def close_database(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
            self.current_db = None
            self.current_table = None
            self.column_filters = {}
            self.db_label.config(text="No database loaded", foreground="gray")
            self.tables_listbox.delete(0, tk.END)
            self.tree.delete(*self.tree.get_children())
            self.table_info_label.config(text="Select a table")
            self.clear_filter_frame()
    
    def refresh_tables(self):
        if not self.conn:
            return
        
        self.tables_listbox.delete(0, tk.END)
        try:
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
            )
            tables = self.cursor.fetchall()
            for table in tables:
                self.tables_listbox.insert(tk.END, table[0])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch tables: {e}")
    
    def on_table_select(self, event):
        selection = self.tables_listbox.curselection()
        if not selection:
            return
        
        table_name = self.tables_listbox.get(selection[0])
        self.current_table = table_name
        self.column_filters = {}
        self.load_table_data(table_name)
    
    def clear_filter_frame(self):
        for widget in self.filter_frame.winfo_children():
            widget.destroy()
    
    def create_filter_widgets(self, columns):
        self.clear_filter_frame()
        self.column_filters = {}
        
        for col in columns:
            frame = ttk.Frame(self.filter_frame)
            frame.pack(side=tk.LEFT, padx=3, pady=2)
            
            ttk.Label(frame, text=f"{col}:", font=("Arial", 8)).pack(side=tk.LEFT, padx=(0, 3))
            
            entry = ttk.Entry(frame, width=8)
            entry.pack(side=tk.LEFT)
            entry.bind("<KeyRelease>", lambda e, c=col: self.on_filter_change(c, e))
            
            self.column_filters[col] = entry
    
    def on_filter_change(self, column, event):
        self.load_table_data(self.current_table)
    
    def load_table_data(self, table_name):
        if not self.conn:
            return
        
        try:
            # Get table info
            self.cursor.execute(f"PRAGMA table_info({table_name});")
            columns = self.cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # Create filter widgets if not already created
            if not self.column_filters:
                self.create_filter_widgets(column_names)
            
            # Build WHERE clause from filters
            where_conditions = []
            for col_name, entry in self.column_filters.items():
                filter_value = entry.get().strip()
                if filter_value:
                    where_conditions.append(f"{col_name} LIKE '%{filter_value}%'")
            
            where_clause = " AND ".join(where_conditions)
            if where_clause:
                query = f"SELECT * FROM {table_name} WHERE {where_clause} LIMIT 1000;"
            else:
                query = f"SELECT * FROM {table_name} LIMIT 1000;"
            
            # Get row count
            if where_clause:
                count_query = f"SELECT COUNT(*) FROM {table_name} WHERE {where_clause};"
            else:
                count_query = f"SELECT COUNT(*) FROM {table_name};"
            
            self.cursor.execute(count_query)
            row_count = self.cursor.fetchone()[0]
            
            self.table_info_label.config(
                text=f"Table: {table_name} | Columns: {len(column_names)} | Rows: {row_count}"
            )
            
            # Clear existing treeview
            self.tree.delete(*self.tree.get_children())
            for col in self.tree['columns']:
                self.tree.heading(col, text="")
            
            # Set up treeview columns
            self.tree['columns'] = column_names
            self.tree.column('#0', width=0, stretch=tk.NO)
            
            for col in column_names:
                self.tree.column(col, anchor=tk.W, width=100)
                self.tree.heading(col, text=col)
            
            # Fetch and display data
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            
            for idx, row in enumerate(rows):
                self.tree.insert(parent='', index='end', iid=idx, values=row)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load table data: {e}")
    
    def execute_query(self):
        if not self.conn:
            messagebox.showwarning("Warning", "No database loaded")
            return
        
        query = self.query_text.get(1.0, tk.END).strip()
        if not query:
            messagebox.showwarning("Warning", "Enter a query")
            return
        
        try:
            self.cursor.execute(query)
            
            # Check if it's a SELECT query
            if query.strip().upper().startswith("SELECT"):
                rows = self.cursor.fetchall()
                columns = [description[0] for description in self.cursor.description]
                
                # Clear treeview
                self.tree.delete(*self.tree.get_children())
                self.tree['columns'] = columns
                self.tree.column('#0', width=0, stretch=tk.NO)
                
                for col in columns:
                    self.tree.column(col, anchor=tk.W, width=100)
                    self.tree.heading(col, text=col)
                
                # Display results
                for idx, row in enumerate(rows):
                    self.tree.insert(parent='', index='end', iid=idx, values=row)
                
                self.table_info_label.config(text=f"Query Results: {len(rows)} rows")
                messagebox.showinfo("Success", f"Query executed: {len(rows)} rows returned")
            else:
                self.conn.commit()
                messagebox.showinfo("Success", "Query executed successfully")
                self.refresh_tables()
        
        except Exception as e:
            messagebox.showerror("Error", f"Query failed: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = SQLiteBrowser(root)
    root.mainloop()