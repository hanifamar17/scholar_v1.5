from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_file,
    jsonify,
    session,
    flash
)
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mysqldb import MySQL
import mysql.connector
import MySQLdb
from flask_cors import CORS
import subprocess
import json
import pandas as pd
import io
import math

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font

import pdfkit




app = Flask(__name__, static_url_path="/static")
app.secret_key = b"\xa9v6\xee5\xd1\xa7pr\x9fh\xb8\xa6{\xbdR<=\x04n\xbc\xdcUT"
CORS(app)

app.config["MYSQL_HOST"] = "127.0.0.1"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "crawlings"

mysql = MySQL(app)


#LOGIN
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM admin WHERE id = %s', (user_id,))
    account = cursor.fetchone()
    if account:
        return User(account['id'], account['username'], account['password'])
    return None

@app.route('/', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM admin WHERE username = %s', (username,))
            account = cursor.fetchone()

            if account and account['password'] == password:  # Pastikan untuk menggunakan hash password di produksi
                user = User(account['id'], account['username'], account['password'])
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password', 'danger')
        return render_template('login.html')
    except MySQLdb.OperationalError as e:
        error_msg = "Terjadi masalah saat mengakses database. Pastikan Database server anda sudah dijalankan."
        return render_template("error-login.html", error=error_msg)

@app.route("/testing", methods=["GET", "POST"])
def testing():
    if request.method == "POST":
        selected_query = request.form.getlist("selected_authors")
        selected = ", ".join(selected_query)

        selected = request.args.get("selected_author")

        # Format string pengembalian untuk debug
        return f"Received author_id: {selected}"


@app.route("/dashboard")
@login_required
def index():
    return render_template("index.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

#ADMIN
@app.route("/admin")
def admin():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""SELECT * FROM admin""")
        data_admin = cur.fetchall()
        cur.close()

        return render_template(
            "admin/admin.html",
            admin=data_admin
        )

    except MySQLdb.OperationalError as e:
        error_msg = "Terjadi masalah saat mengakses database. Pastikan Database server anda sudah dijalankan."
        return render_template("error.html", error=error_msg)

@app.route("/admin/add", methods=["GET", "POST"])
def admin_add():
    return render_template("admin/add.html")

@app.route("/admin/add/submit", methods=["GET", "POST"])
def admin_add_submit():
    username = request.form["username"]
    password = request.form["password"]

    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO admin (username, password) VALUES (%s, %s)", (username, password)
    )
    mysql.connection.commit()
    cur.close()

    flash('Admin berhasil ditambahkan.', 'success')
    return redirect(url_for("admin"))

@app.route("/admin/delete/<int:id>", methods=["POST", "DELETE"])
def admin_delete(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM admin WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()

    flash('Admin berhasil dihapus.', 'success')
    return redirect(url_for("admin"))

@app.route("/admin/update/form/<int:id>", methods=["GET", "POST"])
def admin_update_form(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM admin WHERE id = %s", (id,))
    data_admin = cur.fetchone()
    cur.close()

    return render_template("admin/update-form.html", admin=data_admin)

@app.route("/admin/update/<int:id>", methods=["POST", "GET"])
def admin_update(id):
    username = request.form["username"]
    password = request.form["password"]

    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE admin SET username = %s, password = %s WHERE id = %s",
        (username, password, id),
    )
    mysql.connection.commit()
    cur.close()

    flash('Admin berhasil diperbarui.', 'success')
    return redirect(url_for("admin"))

#PENCARIAN
@app.route("/authors")
def authors():
    with open("output_profiles.json", "r") as profiles:
        data_profiles_json = json.load(profiles)

    return render_template("pencarian/pencarian.html", profiles=data_profiles_json)
    
@app.route("/authors/get_authors", methods=["GET", "POST"])
def get_authors():
    query_profiles = request.form.get("query_profiles").lower()
    spider_name = "dataCrawler_4"

    subprocess.run(["scrapy", "crawl", spider_name, "-o", "output_profiles.json", "-a", f"query_keyword={query_profiles}",])

    with open("output_profiles.json") as profiles:
        data_profiles = json.load(profiles)

    session['data_profiles'] = data_profiles
    session['query_profiles'] = query_profiles

    return redirect(url_for("get_profiles", query=query_profiles))

@app.route("/authors/get_articles", methods=["GET", "POST"])
def get_articles():
    if request.method == "POST":
        selected_query = request.form.getlist("selected_authors")
        selected_query = ",".join(selected_query)
        # return f"Received author name: {selected_query}"
        spider_name = "dataCrawler_3"
        subprocess.run(["scrapy", "crawl", spider_name, "-o", "output.json", "-a", f"author_id={selected_query}",])

        with open("output.json") as items_file:
            data_articles = json.load(items_file)

        with open("output_profiles.json") as profiles:
            data_profiles_json = json.load(profiles)
        
        #return render_template(
        #    "pencarian/get_profiles.html", output=data_articles, profiles=data_profiles_json
        #)
        return redirect(url_for('results'))
    else:
        selected_query = request.args.get("selected_author")
        # return f"Received author name: {selected_query}"
        spider_name = "dataCrawler_3"
        subprocess.run(["scrapy", "crawl", spider_name, "-o", "output.json", "-a", f"author_id={selected_query}",])

        with open("output.json") as items_file:
            data_articles = json.load(items_file)

        with open("output_profiles.json") as profiles:
            data_profiles_json = json.load(profiles)
        
        #return render_template(
         #   "pencarian/get_profiles.html", output=data_articles, profiles=data_profiles_json
        #)
        return redirect(url_for('results'))

@app.route("/authors/get_profiles")
def get_profiles():
    query_param = request.args.get('query', '-')
    query_profiles = [query.strip() for query in query_param.split(',')]

    #query_profiles = session.get("query_profiles", "-")
    data_profiles = session.get("data_profiles", "-")
    not_found_queries = []
    

    try:
        with open("output_profiles.json") as profiles:
            data_profiles_json = profiles.read()
            data_profiles_json = json.loads(data_profiles_json)

            names = [profile.get('name', '').lower() for profile in data_profiles_json]
            for query in query_profiles:
                if not any(query.lower() in name for name in names):
                    not_found_queries.append(query)

            if not_found_queries:                
                raise ValueError(f"Tidak ditemukan hasil pencarian untuk")

            return render_template("pencarian/get_profiles.html", profiles=data_profiles)
    
    except ValueError as ve:
        not_found_queries_str = ', '.join(not_found_queries)
        return render_template('pencarian/get_profiles.html', error_message=str(ve), query_profiles=not_found_queries_str, profiles=data_profiles)
    
@app.route("/authors/history_get_articles")
def history_get_articles():
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT query, GROUP_CONCAT(thumbnail) AS thumbnail, MAX(updated_at) AS updated_at "
            "FROM publikasi "
            "GROUP BY query "
            "ORDER BY updated_at DESC"
        )
        authors = cur.fetchall()

        author_data = []
        for author in authors:
            query = author[0].lower()
            thumbnail = author[1]
            updated_at = author[2]

            updated_at = updated_at.strftime("%d-%m-%Y %H:%M:%S")

            cur.execute(
                "SELECT prodi FROM dosen WHERE LOWER(nama_dosen) = %s", (query,)
            )
            result = cur.fetchone()

            if result:
                prodi = result[0]
            else:
                prodi = "-"

            author_data.append(
                {
                    "query": query,
                    "thumbnail": thumbnail,
                    "prodi": prodi,
                    "updated_at": updated_at,
                }
            )

        cur.close()
        return render_template("pencarian/history_get_articles.html", history=author_data)

    except MySQLdb.OperationalError as e:
        error_msg = "Terjadi masalah saat mengakses database. Pastikan Database server anda sudah dijalankan."
        return render_template("error.html", error=error_msg)


#HASIL PENCARIAN
@app.route("/results", methods=["GET", "POST"])
def results():
    page = request.args.get("page", 1, type=int)

    if request.method == "POST":
        per_page = int(request.form.get("per_page", "10"))
        return redirect(url_for('results', per_page=per_page, page=1))
    else:
        per_page = int(request.args.get("per_page", "10"))

    with open("output.json", "r") as f:
        data = json.load(f)

     # Ganti nilai None dengan 0
    for item in data:
        for key, value in item.items():
            if value is None:
                item[key] = 0

    # Dapatkan semua query yang unik
    queries = set(item["query"].lower() for item in data if "query" in item)
    queries = list(queries)

    # for entry in data:
    #   entry['title'] = entry['title'][0] if entry['title'] else ""

    data_sorted = sorted(data, key=lambda x: x["query"])    

    # Tentukan jumlah data per halaman
    total = len(data_sorted)
    total_pages = math.ceil(total / per_page)

    # Tentukan batasan data untuk halaman saat ini
    start = (page - 1) * per_page
    end = start + per_page
    paginated_data = data_sorted[start:end]

    return render_template(
        "results/results.html",
        value=paginated_data,
        queries=queries,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@app.route("/all_results", methods=["GET", "POST"])
def all_results():
    try:
        page = request.args.get("page", default=1, type=int)

        if request.method == "POST":
            per_page = int(request.form.get("per_page", "10"))
            return redirect(url_for('all_results', per_page=per_page, page=1))
        else:
            per_page = int(request.args.get("per_page", "10"))
        offset = (page - 1) * per_page

        sort_by_query = request.args.get("sortQuery", default="query", type=str)
        sort_order_query = request.args.get("orderQuery", default="asc", type=str)

        sort_by_year = request.args.get("sortYear", default="publication_year", type=str)
        sort_order_year = request.args.get("orderYear", default="asc", type=str)

        # Buat klausa ORDER BY untuk pengurutan
        order_clause = f"ORDER BY {sort_by_query} {sort_order_query}, {sort_by_year} {sort_order_year}"

        # Query data dari database dengan filter dan paginasi
        query = (
            f"SELECT * FROM publikasi {order_clause} LIMIT {per_page} OFFSET {offset}"
        )

        cur = mysql.connection.cursor()
        cur.execute(query)
        # cur.execute('''SELECT author, title, publication_year, link FROM crawlings''')
        data = cur.fetchall()

        # mengganti nilai None dengan '0'
        data = [[0 if value is None else value for value in row] for row in data]
        
        # Hitung total data untuk paginasi
        total_data_query = f"SELECT COUNT(*) FROM publikasi"
        cur.execute(total_data_query)
        total_data = cur.fetchone()[0]


        # hitung total halaman
        total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)
        cur.close()
        return render_template(
            "results/all_results.html",
            values=data,
            total_pages=total_pages,
            current_page=page,
            page=page,
            per_page=per_page,
            sort_by_query=sort_by_query,
            sort_order_query=sort_order_query,
            sort_by_year=sort_by_year,
            sort_order_year=sort_order_year
        )
    except MySQLdb.OperationalError as e:
        error_msg = "Terjadi masalah saat mengakses database. Pastikan Database server anda sudah dijalankan."
        return render_template("error.html", error=error_msg)

@app.route("/results/preview_pdf")
def preview_pdf():
    with open("output.json", "r") as file_json:
        data_json = json.load(file_json)
        # Mengganti nilai None dengan 0
        for entry in data_json:
            for key, value in entry.items():
                if value is None:
                    entry[key] = 0

    # for entry in data_json:
    #   entry['title'] = entry['title'][0] if entry['title'] else ""

    rendered = render_template("template/template_pdf.html", data_json=data_json)

    config = pdfkit.configuration(
        wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"
    )

    options = {
        "enable-local-file-access": None,
        "page-size": "A4",
        "page-width": "210mm",
        "page-height": "330mm",
        "margin-top": "20mm",
        "margin-right": "20mm",
        "margin-bottom": "20mm",
        "margin-left": "20mm",
    }
    pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)

    return send_file(
        io.BytesIO(pdf),
        mimetype="application/pdf",
        as_attachment=False,
        download_name="preview.pdf",
    )

@app.route("/results/download/excel")
def download_excel():
    page = request.args.get("page", 1, type=int)

    with open("output.json", "r") as f:
        data = json.load(f)

    data_sorted = sorted(data, key=lambda x: x["query"])

    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(data_sorted)

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")

    output.seek(0)
    wb = load_workbook(output)
    ws = wb.active

    # Set alignment and font for the header row
    for cell in ws[1]:
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.font = Font(bold=True)

    # Adjust column widths
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = max_length + 2
        ws.column_dimensions[column].width = adjusted_width

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        download_name="Hasil_crawling.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

@app.route("/results/search-data-json", methods=["GET", "POST"])
def search_data_json():
    search_query = request.form.get("search_query")

    with open("output.json", "r") as f:
        data_json = json.load(f)

    # for entry in data_json:
    #   entry['title'] = entry['title'][0] if entry['title'] else ""

    search_results = [
        item
        for item in data_json
        if search_query.lower() in item["query"]
        or search_query.lower() in item["author"]
        or search_query.lower() in item["title"]
        or search_query.lower() in item["cited_by_value"]
        or search_query.lower() in item["publication_year"]
    ]

    return jsonify(search_results)

@app.route("/all_results/download/excel")
def all_results_download_excel():
    page = request.args.get("page", 1, type=int)

    cur = mysql.connection.cursor()
    cur.execute(
        """SELECT query, author, title, title_url, cited_by_value, cited_by_url, publication_year FROM publikasi"""
    )
    values = cur.fetchall()
    cur.close()

    # Convert the list of tuples to a list of dictionaries
    columns = [
        "query",
        "author",
        "title",
        "title_url",
        "cited_by_value",
        "cited_by_url",
        "publication_year",
    ]
    data_sorted = sorted(
        [dict(zip(columns, row)) for row in values], key=lambda x: x["query"].lower()
    )

    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(data_sorted)

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")

    output.seek(0)
    wb = load_workbook(output)
    ws = wb.active

    # Set alignment and font for the header row
    for cell in ws[1]:
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.font = Font(bold=True)

    # Adjust column widths
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = max_length + 2
        ws.column_dimensions[column].width = adjusted_width

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        download_name="Hasil_crawling.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

@app.route("/all_results/preview_pdf")
def all_results_preview_pdf():
    cur = mysql.connection.cursor()
    cur.execute(
        """SELECT query, author, title, title_url, cited_by_value, cited_by_url, publication_year FROM publikasi ORDER BY author ASC"""
    )
    data = cur.fetchall()

    # mengganti nilai None dengan '0'
    data = [[0 if value is None else value for value in row] for row in data]

    cur.close()

    # for entry in data_json:
    #   entry['title'] = entry['title'][0] if entry['title'] else ""

    rendered = render_template("template/template_pdf_database.html", database=data)

    config = pdfkit.configuration(
        wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"
    )

    options = {
        "enable-local-file-access": None,
        "page-size": "A4",
        "page-width": "210mm",
        "page-height": "330mm",
        "margin-top": "20mm",
        "margin-right": "20mm",
        "margin-bottom": "20mm",
        "margin-left": "20mm",
    }
    pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)

    return send_file(
        io.BytesIO(pdf),
        mimetype="application/pdf",
        as_attachment=False,
        download_name="preview.pdf",
    )


#ALL_RESULTS/PENCARIAN
@app.route("/all_results/search-author", methods=["GET", "POST"])
def all_results_search_author():
    page = request.args.get("page", default=1, type=int)
    author = request.args.get("query", "")
    session['get_author']=author

    if request.method == "POST":
        per_page = int(request.form.get("per_page", "10"))
        author = request.form.get("query", "")
        return redirect(url_for('all_results_search_author', per_page=per_page, page=1, query=author))
    else:
        per_page = int(request.args.get("per_page", "10"))
        author = request.args.get("query", "")
    offset = (page - 1) * per_page

    sort_by_query = request.args.get("sortQuery", default="query", type=str)
    sort_order_query = request.args.get("orderQuery", default="asc", type=str)

    sort_by_year = request.args.get("sortYear", default="publication_year", type=str)
    sort_order_year = request.args.get("orderYear", default="asc", type=str)

    # Buat klausa ORDER BY untuk pengurutan
    order_clause = f"ORDER BY {sort_by_query} {sort_order_query}, {sort_by_year} {sort_order_year}"
    
    query = f"SELECT * FROM publikasi WHERE query = %s {order_clause} LIMIT %s OFFSET %s"

    cur = mysql.connection.cursor()
    cur.execute(query, (author, per_page, offset))
    data = cur.fetchall()

    # mengganti nilai None dengan '0'
    data = [[0 if value is None else value for value in row] for row in data]

    total_data_query = "SELECT COUNT(*) FROM publikasi WHERE query = %s"
    cur.execute(total_data_query, (author,))
    total_data = cur.fetchone()[0]

    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)

    return render_template(
        "results/search_author_results.html",
        search_value=data,
        author=author,
        page=page,
        total_pages=total_pages,
        per_page=per_page,
        sort_by_query=sort_by_query,
        sort_order_query=sort_order_query,
        sort_by_year=sort_by_year,
        sort_order_year=sort_order_year
    )

@app.route("/search-author", methods=["GET"])
def search_author():
    author = request.args.get("query", "").lower()

    cur = mysql.connection.cursor()
    if author:
        cur.execute(
            "SELECT query FROM publikasi WHERE query LIKE %s ORDER BY query ASC", ("%" + author + "%",)
        )
    else:
        cur.execute("SELECT query FROM publikasi ORDER BY query ASC")
    author = cur.fetchall()
    cur.close()

    results = list(set([result[0] for result in author]))
    results.sort()

    return jsonify(results)

@app.route("/all_results/search-author/download/excel", methods=["GET", "POST"])
def search_author_download_excel():
    author = request.args.get("query", "")

    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT query, author, title, title_url, cited_by_value, cited_by_url, publication_year FROM publikasi WHERE query = %s",
        (author,),
    )
    values = cur.fetchall()
    cur.close()

    columns = [
        "query",
        "author",
        "title",
        "title_url",
        "cited_by_value",
        "cited_by_url",
        "publication_year",
    ]
    data_sorted = sorted(
        [dict(zip(columns, row)) for row in values], key=lambda x: x["author"].lower()
    )

    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(data_sorted)

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")

    output.seek(0)
    wb = load_workbook(output)
    ws = wb.active

    # Set alignment and font for the header row
    for cell in ws[1]:
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.font = Font(bold=True)

    # Adjust column widths
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = max_length + 2
        ws.column_dimensions[column].width = adjusted_width

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        download_name="Hasil_crawling.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

@app.route("/all_results/search-author/preview_pdf", methods=["GET"])
def search_author_preview_pdf():
    author = request.args.get("query", "")

    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT query, author, title, title_url, cited_by_value, cited_by_url, publication_year FROM publikasi WHERE query = %s ORDER BY author ASC",
        (author,),
    )
    data = cur.fetchall()

    # mengganti nilai None dengan '0'
    data = [[0 if value is None else value for value in row] for row in data]

    cur.close()

    # for entry in data_json:
    #   entry['title'] = entry['title'][0] if entry['title'] else ""

    rendered = render_template("template/template_pdf_search.html", query=data)

    config = pdfkit.configuration(
        wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"
    )

    options = {
        "enable-local-file-access": None,
        "page-size": "A4",
        "page-width": "210mm",
        "page-height": "330mm",
        "margin-top": "20mm",
        "margin-right": "20mm",
        "margin-bottom": "20mm",
        "margin-left": "20mm",
    }
    pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)

    return send_file(
        io.BytesIO(pdf),
        mimetype="application/pdf",
        as_attachment=False,
        download_name="preview.pdf",
    )

@app.route("/all_results/search_bar", methods=["GET", "POST"])
def search_bar():
    page = request.args.get("page", default=1, type=int)
    search_query = request.args.get("search", "").lower()

    if request.method == "POST":
        per_page = int(request.form.get("per_page", "10"))
        search_query = request.args.get("search", "").lower()
        return redirect(url_for('search_bar', per_page=per_page, page=1, search_query=search_query))
    else:
        per_page = int(request.args.get("per_page", "10"))
        search_query = request.args.get("search", "").lower()
    offset = (page - 1) * per_page

    sort_by_query = request.args.get("sortQuery", default="query", type=str)
    sort_order_query = request.args.get("orderQuery", default="asc", type=str)

    sort_by_cite = request.args.get("sortCite", default="cited_by_value", type=str)
    sort_order_cite = request.args.get("orderCite", default="asc", type=str)

    sort_by_year = request.args.get("sortYear", default="publication_year", type=str)
    sort_order_year = request.args.get("orderYear", default="asc", type=str)

    per_page = 10
    offset = (page - 1) * per_page

    # klausa WHERE untuk filter author
    search_clause = f"LOWER(query) LIKE %s OR LOWER(author) LIKE %s OR LOWER(title) LIKE %s OR publication_year LIKE %s"
    search_values = (
        "%" + search_query + "%",
        "%" + search_query + "%",
        "%" + search_query + "%",
        "%" + search_query + "%",
    )

    # Buat klausa ORDER BY untuk pengurutan
    order_clause = f"ORDER BY {sort_by_query} {sort_order_query}, {sort_by_cite} {sort_order_cite}, {sort_by_year} {sort_order_year}"

    # Gabungkan klausa ORDER BY dengan klausa WHERE
    query = f"SELECT * FROM publikasi WHERE {search_clause} {order_clause} LIMIT {per_page} OFFSET {offset}"

    cur = mysql.connection.cursor()
    cur.execute(query, search_values)
    data = cur.fetchall()

    # mengganti nilai None dengan '0'
    data = [[0 if value is None else value for value in row] for row in data]


    # Hitung total data untuk paginasi
    total_data_query = f"SELECT COUNT(*) FROM publikasi WHERE {search_clause}"
    cur.execute(total_data_query, search_values)
    total_data = cur.fetchone()[0]

    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)

    return render_template(
        "results/search_bar_results.html",
        search_value=data,
        search_query=search_query,
        total_pages=total_pages,
        page=page,
        per_page=per_page,
        sort_by_query=sort_by_query,
        sort_order_query=sort_order_query,
        sort_by_cite=sort_by_cite,
        sort_order_cite=sort_order_cite,
        sort_by_year=sort_by_year,
        sort_order_year=sort_order_year,
    )


#DOSEN
@app.route("/dosen")
def dosen():
    try:
        page = request.args.get("page", 1, type=int)
        cur = mysql.connection.cursor()
        cur.execute("""SELECT * FROM dosen""")
        data_dosen = cur.fetchall()
        cur.close()

        # Tentukan jumlah data per halaman
        per_page = 10
        total = len(data_dosen)
        total_pages = math.ceil(total / per_page)

        # Tentukan batasan data untuk halaman saat ini
        start = (page - 1) * per_page
        end = start + per_page
        paginated_data = data_dosen[start:end]

        return render_template(
            "/dosen/dosen.html",
            dosen=paginated_data,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )

    except MySQLdb.OperationalError as e:
        error_msg = "Terjadi masalah saat mengakses database. Pastikan Database server anda sudah dijalankan."
        return render_template("error.html", error=error_msg)

@app.route("/dosen/add", methods=["GET", "POST"])
def dosen_add():
    return render_template("dosen/add.html")

@app.route("/dosen/add/submit", methods=["GET", "POST"])
def dosen_add_submit():
    nama_dosen = request.form["nama_dosen"]
    prodi = request.form["prodi"]

    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO dosen (nama_dosen, prodi) VALUES (%s, %s)", (nama_dosen, prodi)
    )
    mysql.connection.commit()
    cur.close()

    flash('Dosen berhasil ditambahkan.', 'success')
    return redirect(url_for("dosen"))

@app.route("/dosen/delete/<int:id>", methods=["POST", "DELETE"])
def dosen_delete(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM dosen WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()

    flash('Dosen berhasil dihapus.', 'success')
    return redirect(url_for("dosen"))

@app.route("/dosen/update/form/<int:id>", methods=["GET", "POST"])
def dosen_update_form(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM dosen WHERE id = %s", (id,))
    dosen = cur.fetchone()
    cur.close()

    return render_template("dosen/update-form.html", dosen=dosen)

@app.route("/dosen/update/<int:id>", methods=["POST", "GET"])
def dosen_update(id):
    nama_dosen = request.form["nama_dosen"]
    prodi = request.form["prodi"]

    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE dosen SET nama_dosen = %s, prodi = %s WHERE id = %s",
        (nama_dosen, prodi, id),
    )
    mysql.connection.commit()
    cur.close()

    flash('Dosen berhasil diperbarui.', 'success')
    return redirect(url_for("dosen"))

@app.route("/dosen/import", methods=["GET", "POST"])
def dosen_import():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part"

        file = request.files["file"]

        if file.filename == "":
            return "No selected file"

        df = pd.read_excel(file)

        cur = mysql.connection.cursor()
        for index, row in df.iterrows():
            cur.execute(
                "INSERT INTO dosen (nama_dosen, prodi) VALUES (%s, %s)",
                (row["nama_dosen"], row["prodi"]),
            )
        mysql.connection.commit()
        cur.close()

        flash('Dosen berhasil diimport.', 'success')
        return redirect(url_for("dosen"))
    return redirect(url_for("dosen"))



#AUTOCOMPLETE
@app.route("/search-query", methods=["GET"])
def search_query():
    query = request.args.get("nama", "")

    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT nama_dosen as query FROM dosen WHERE nama_dosen LIKE %s",
        ("%" + query + "%",),
    )
    results = cur.fetchall()
    cur.close()
    return jsonify([result[0] for result in results])


#OTHERS
@app.route("/search_bar_author", methods=["GET", "POST"])
def search_bar_author():
    page = request.args.get("page", default=1, type=int)
    search_query = request.args.get("search", "").lower()
    query_param = request.args.get("author", "").lower()
    author = session.get("get_author", "-")

    sort_by_query = request.args.get("sortQuery", default="query", type=str)
    sort_order_query = request.args.get("orderQuery", default="asc", type=str)

    sort_by_cite = request.args.get("sortCite", default="cited_by_value", type=str)
    sort_order_cite = request.args.get("orderCite", default="asc", type=str)

    sort_by_year = request.args.get("sortYear", default="publication_year", type=str)
    sort_order_year = request.args.get("orderYear", default="asc", type=str)

    per_page = 10
    offset = (page - 1) * per_page

    # klausa WHERE untuk filter author
    search_clause = f"(LOWER(author) LIKE %s OR LOWER(title) LIKE %s OR publication_year LIKE %s) AND LOWER(query) LIKE %s"
    search_values = (
        "%" + search_query + "%",
        "%" + search_query + "%",
        "%" + search_query + "%",
        "%" + query_param + "%"
    )

    # Buat klausa ORDER BY untuk pengurutan
    order_clause = f"ORDER BY {sort_by_query} {sort_order_query}, {sort_by_cite} {sort_order_cite}, {sort_by_year} {sort_order_year}"

    # Gabungkan klausa ORDER BY dengan klausa WHERE
    query = f"SELECT * FROM publikasi WHERE {search_clause} {order_clause} LIMIT {per_page} OFFSET {offset}"

    cur = mysql.connection.cursor()
    cur.execute(query, search_values)
    data = cur.fetchall()

    # mengganti nilai None dengan '-'
    sanitized_values = []
    for row in data:
        sanitized_row = [(value if value is not None else '-') for value in row]
        sanitized_values.append(sanitized_row)

    # Hitung total data untuk paginasi
    total_data_query = f"SELECT COUNT(*) FROM publikasi WHERE {search_clause}"
    cur.execute(total_data_query, search_values)
    total_data = cur.fetchone()[0]

    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)

    return render_template(
        "results/search_bar_author.html",
        author=author,
        search_value=sanitized_values,
        search_query=search_query,
        total_pages=total_pages,
        page=page,
        per_page=per_page,
        sort_by_query=sort_by_query,
        sort_order_query=sort_order_query,
        sort_by_cite=sort_by_cite,
        sort_order_cite=sort_order_cite,
        sort_by_year=sort_by_year,
        sort_order_year=sort_order_year,
    )

@app.route("/author-crawling", methods=["POST", "GET"])
def author_crawling():
    spider_name = "dosenCrawler"

    subprocess.run(["scrapy", "crawl", spider_name, "-o", "output_dosen.json"])

    with open("output.json") as items_file:
        return render_template("author.html", author_output=items_file.read())



app.run(debug=True, host="0.0.0.0", port=4040)
