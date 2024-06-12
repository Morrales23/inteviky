from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
csrf = CSRFProtect()
app.secret_key = 'supersecretkey'







#Conexion a la base de datos 

def get_db_connection():
    connection = psycopg2.connect(
        host='localhost',
        user='postgres',
        password='TheScott23',
        database='bsviky'
    )
    return connection





#Login e inicio de sesion 

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        contraseña = request.form.get('contraseña')

        if not nombre or not contraseña:
            error = 'Nombre y contraseña son requeridos'
        else:
            try:
                connection = get_db_connection()
                cursor = connection.cursor()
                cursor.execute("SELECT id_empleado, rol FROM usuarios WHERE nombre = %s AND contraseña = %s", (nombre, contraseña))
                user = cursor.fetchone()
                cursor.close()
                connection.close()

                if user:
                    session['user_id'] = user[0]
                    session['user_role'] = user[1]
                    return redirect(url_for('index'))
                else:
                    error = 'Nombre o contraseña incorrectos'
            except Exception as ex:
                print(ex)
                error = 'Ha ocurrido un error. Inténtalo de nuevo.'
    return render_template('login.html', error=error)


@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('index.html')
    return redirect(url_for('login'))






#Vistas a las tablas de usuarios, productos, categorias y proveedores

@app.route('/usuarios')
def usuarios():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM usuarios")
        usuarios = cursor.fetchall()
    except Exception as ex:
        print(ex)
        usuarios = []
    finally:
        if connection:
            connection.close()
    
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/productos')
def productos():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT p.nombre AS producto, p.marca, p.stock, p.precio, c.nombre AS categoria 
            FROM productos p 
            INNER JOIN categorias c ON p.id_categoria = c.id_categoria
        """)
        productos = cursor.fetchall()
        cursor.close()  
    except Exception as ex:
        print(ex)
        productos = []
    finally:
        if connection:
            connection.close()  
    
    return render_template('productos.html', productos=productos)

@app.route('/categorias')
def categorias():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM categorias")
        categorias = cursor.fetchall()
    except Exception as ex:
        print(ex)
        categorias = []
    finally:
        if connection:
            connection.close()
    
    return render_template('categorias.html', categorias=categorias)

@app.route('/proveedores')
def proveedores():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM proveedores")
        proveedores = cursor.fetchall()
    except Exception as ex:
        print(ex)
        proveedores = []
    finally:
        if connection:
            connection.close()
    
    return render_template('proveedores.html', proveedores=proveedores)


#Editar CRUDS


@app.route('/proveedores/editar/<int:id>', methods=['GET', 'POST'])
def editar_proveedor(id):
    if request.method == 'POST':
        contacto = request.form.get('contacto')
        dia_pedido = request.form.get('dia_pedido')
        dia_entrega = request.form.get('dia_entrega')
        total_pagado = request.form.get('total_pagado')
        id_producto = request.form.get('id_producto')

        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE proveedores
                SET contacto = %s, dia_pedido = %s, dia_entrega = %s, total_pagado = %s, id_producto = %s
                WHERE id_proveedor = %s
            """, (contacto, dia_pedido, dia_entrega, total_pagado, id_producto, id))
            connection.commit()
            cursor.close()
            connection.close()
            flash('Proveedor actualizado exitosamente')
            return redirect(url_for('proveedores'))
        except Exception as ex:
            print(ex)
            flash('Ha ocurrido un error. Inténtalo de nuevo.')
            return redirect(url_for('editar_proveedor', id=id))
    else:
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM proveedores WHERE id_proveedor = %s", (id,))
            proveedor = cursor.fetchone()
            cursor.close()
            connection.close()
            if proveedor:
                return render_template('editar_proveedor.html', proveedor=proveedor)
            else:
                flash('Proveedor no encontrado')
                return redirect(url_for('proveedores'))
        except Exception as ex:
            print(ex)
            flash('Ha ocurrido un error. Inténtalo de nuevo.')
            return redirect(url_for('proveedores'))



#CRUDS

@app.route('/iniciar_turno', methods=['GET', 'POST'])
def iniciar_turno():
    return render_template('iniciar_turno.html')

@app.route('/registrar_venta', methods=['POST'])
def registrar_venta():
    return redirect(url_for('index'))

@app.route('/finalizar_turno', methods=['POST'])
def finalizar_turno():
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

if __name__ == '__main__':
    csrf.init_app(app)
    app.run(debug=True)
