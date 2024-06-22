from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
from flask_wtf.csrf import CSRFProtect
from functools import wraps


app = Flask(__name__)



csrf = CSRFProtect()
csrf.init_app(app)
app.secret_key = 'supersecretkey'
app.template_folder = 'templates'
app.static_folder = 'static'


# Conexion a la base de datos
def get_db_connection():
    connection = psycopg2.connect(
        host='localhost',
        user='postgres',
        password='TheScott23',
        database='bsviky'
    )
    return connection


#Roles
def role_required(required_role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'user_role' in session and session['user_role'] == 'cajero':
                flash('Acceso no autorizado. No tienes permisos para acceder a esta página.')
                return render_template('acceso.html')
            return func(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_role', None)
    flash('Sesión cerrada exitosamente')
    return redirect(url_for('login'))

# Login e inicio de sesion
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


# Vistas

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
            SELECT pd.id_producto, pd.nombre, pd.marca, pd.stock, pd.precio, ct.nombre AS categoria
            FROM productos pd
            LEFT JOIN categorias ct ON pd.id_categoria = ct.id_categoria
        """)
        productos = cursor.fetchall()
    except Exception as ex:
        print(ex)
        productos = []
    finally:
        if connection:
            connection.close()

            print(session)  # Puedes agregar esto en alguna parte de tu código Flask para debug


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


# Editar

@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
@role_required('cajero')
def editar_usuario(id):
    if request.method == 'POST':
        nombre = request.form['nombre']
        contraseña = request.form['contraseña']
        rol = request.form['rol']

        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE usuarios SET nombre = %s, contraseña = %s, rol = %s WHERE id_empleado = %s",
                (nombre, contraseña, rol, id)
            )
            connection.commit()
            flash('Usuario actualizado exitosamente')
        except Exception as ex:
            print(ex)
            flash('Error al actualizar el Usuario')
        finally:
            if connection:
                connection.close()

        return redirect(url_for('usuarios'))

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE id_empleado = %s", (id,))
        usuario = cursor.fetchone()
    except Exception as ex:
        print(ex)
        usuario = None
    finally:
        if connection:
            connection.close()

    form = {
        'nombre': usuario[1] if usuario else '',
        'contraseña': usuario[2] if usuario else '',
        'rol': usuario[3] if usuario else ''
    }

    return render_template('editar_usuario.html', form=form)


@app.route('/proveedores/editar/<int:id>', methods=['GET', 'POST'])
@role_required('cajero')
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
        print(user_role)


@app.route('/editar_producto/<int:id>', methods=['GET', 'POST'])
@role_required('cajero')
def editar_producto(id):
    if request.method == 'POST':
        nombre = request.form['nombre']
        marca = request.form['marca']
        stock = request.form['stock']
        precio = request.form['precio']
        id_categoria = request.form['id_categoria']

        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE productos
                SET nombre = %s, marca = %s, stock = %s, precio = %s, id_categoria = %s
                WHERE id_producto = %s
            """, (nombre, marca, stock, precio, id_categoria, id))
            connection.commit()
        except Exception as ex:
            print(ex)
        finally:
            if connection:
                connection.close()

        return redirect(url_for('productos'))

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM productos WHERE id_producto = %s", (id,))
        producto = cursor.fetchone()
    except Exception as ex:
        print(ex)
        producto = None
    finally:
        if connection:
            connection.close()

        form = {
            'nombre': producto[1] if producto else '',
            'marca': producto[2] if producto else '',
            'stock': producto[3] if producto else '',
            'precio': producto[4] if producto else '',
        }

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id_categoria, nombre FROM categorias")
        categorias = cursor.fetchall()
    except Exception as ex:
        print(ex)
        categorias = []
    finally:
        if connection:
            connection.close()
        

    return render_template('editar_producto.html', form=form, categorias=categorias)




@app.route('/editar_categoria/<int:id>', methods=['GET', 'POST'])
@role_required('cajero')
def editar_categoria(id):
    if request.method == 'POST':
        nombre = request.form['nombre']
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute('UPDATE categorias SET nombre = %s WHERE id_categoria = %s', (nombre, id))
            connection.commit()
            flash('Categoría actualizada exitosamente')
            return redirect(url_for('categorias'))
        except Exception as ex:
            print(ex)
            flash('Error al actualizar la categoría')
        finally:
            if connection:
                connection.close()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM categorias WHERE id_categoria = %s', (id,))
        categoria = cursor.fetchone()
    except Exception as ex:
        print(ex)
        categoria = None
    finally:
        if connection:
            connection.close()

    form = {
        'nombre': categoria[1] if categoria else '',
    }

    return render_template('editar_categoria.html', form=form)


# Crear

@app.route('/nuevo_proveedor', methods=['GET', 'POST'])
@role_required('cajero')
def nuevo_proveedor():
    if request.method == 'POST':
        contacto = request.form['contacto']
        dia_pedido = request.form['dia_pedido']
        dia_entrega = request.form['dia_entrega']
        total_pagado = request.form['total_pagado']

        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO proveedores (contacto, dia_pedido, dia_entrega, total_pagado) VALUES (%s, %s, %s, %s)",
                (contacto, dia_pedido, dia_entrega, total_pagado)
            )
            connection.commit()
            flash('Proveedor agregado exitosamente')
        except Exception as ex:
            print(ex)
            flash('Error al agregar el proveedor')
        finally:
            if connection:
                connection.close()

        return redirect(url_for('proveedores'))

    return render_template('nuevo_proveedor.html')


@app.route('/nuevo_usuario', methods=['GET', 'POST'])
@role_required('cajero')
def nuevo_usuario():
    if request.method == 'POST':
        nombre = request.form['nombre']
        contraseña = request.form['contraseña']
        rol = request.form['rol']

        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO usuarios (nombre, contraseña, rol) VALUES (%s, %s, %s)",
                (nombre, contraseña, rol)
            )
            connection.commit()
            flash('Usuario agregado exitosamente')
        except Exception as ex:
            print(ex)
            flash('Error al agregar el Usuario')
        finally:
            if connection:
                connection.close()

        return redirect(url_for('usuarios'))
    return render_template('nuevo_usuario.html')


@app.route('/nuevo_producto', methods=['GET', 'POST'])
@role_required('cajero')
def nuevo_producto():
    if request.method == 'POST':
        nombre = request.form['nombre']
        marca = request.form['marca']
        stock = request.form['stock']
        precio = request.form['precio']
        id_categoria = request.form['id_categoria']

        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO productos (nombre, marca, stock, precio, id_categoria) VALUES (%s, %s, %s, %s, %s)",
                (nombre, marca, stock, precio, id_categoria)
            )
            connection.commit()
            flash('Producto agregado exitosamente')
        except Exception as ex:
            print(ex)
            flash('Error al agregar el producto')
        finally:
            if connection:
                connection.close()

        return redirect(url_for('productos'))
    

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id_categoria, nombre FROM categorias")
        categorias = cursor.fetchall()
    except Exception as ex:
        print(ex)
        categorias = []
    finally:
        if connection:
            connection.close()

    return render_template('nuevo_producto.html', categorias=categorias)



@app.route('/nueva_categoria', methods=['GET', 'POST'])
@role_required('cajero')
def nueva_categoria():
    if request.method == 'POST':
        nombre = request.form['nombre']

        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO categorias (nombre) VALUES (%s)",
                (nombre,)
            )
            connection.commit()
            flash('Categoría agregada exitosamente')
        except Exception as ex:
            print(ex)
            flash('Error al agregar la categoría')
        finally:
            if connection:
                connection.close()

        return redirect(url_for('categorias'))

    return render_template('nueva_categoria.html')


# Eliminar

@app.route('/eliminar_usuario/<int:id>', methods=['POST'])
@role_required('cajero')
def eliminar_usuario(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM usuarios WHERE id_empleado = %s", (id,))
        connection.commit()
        flash('Usuario eliminado exitosamente')
    except Exception as ex:
        print(ex)
        flash('Error al eliminar el Usuario')
    finally:
        if connection:
            connection.close()

    return redirect(url_for('usuarios'))


@app.route('/eliminar_producto/<int:id>', methods=['POST'])
@role_required('cajero')
def eliminar_producto(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM productos WHERE id_producto = %s", (id,))
        connection.commit()
        flash('Producto eliminado exitosamente')
    except Exception as ex:
        print(ex)
        flash('Error al eliminar el Producto')
    finally:
        if connection:
            connection.close()
    return redirect(url_for('productos'))


@app.route('/eliminar_categoria/<int:id>', methods=['POST'])
@role_required('cajero')
def eliminar_categoria(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM categorias WHERE id_categoria = %s", (id,))
        connection.commit()
        flash('Categoría eliminada exitosamente')
    except Exception as ex:
        print(ex)
        flash('Error al eliminar la Categoría')
    finally:
        if connection:
            connection.close()
    return redirect(url_for('categorias'))


@app.route('/eliminar_proveedor/<int:id>', methods=['POST'])
@role_required('cajero')
def eliminar_proveedor(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM proveedores WHERE id_proveedor = %s", (id,))
        connection.commit()
        flash('Proveedor eliminado exitosamente')
    except Exception as ex:
        print(ex)
        flash('Error al eliminar el Proveedor')
    finally:
        if connection:
            connection.close()
    return redirect(url_for('proveedores'))



#Ventas 

@app.route('/ventas')
def ventas():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT v.id_venta, v.fecha, v.total, u.nombre AS empleado
            FROM ventas v
            JOIN usuarios u ON v.id_empleado = u.id_empleado
        """)
        ventas = cursor.fetchall()
    except Exception as ex:
        print(ex)
        ventas = []
    finally:
        if connection:
            connection.close()

    return render_template('ventas.html', ventas=ventas)


@app.route('/nueva_venta', methods=['GET', 'POST'])
@role_required('cajero')
def nueva_venta():
    if request.method == 'POST':
        productos = request.form.getlist('productos')
        cantidades = request.form.getlist('cantidades')
        precios = request.form.getlist('precios')
        total = request.form['total']
        id_empleado = session.get('user_id')

        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("INSERT INTO ventas (total, id_empleado) VALUES (%s, %s) RETURNING id_venta", (total, id_empleado))
            id_venta = cursor.fetchone()[0]

            for producto, cantidad, precio in zip(productos, cantidades, precios):
                subtotal = float(cantidad) * float(precio)
                cursor.execute("""
                    INSERT INTO detalle_venta (id_venta, id_producto, cantidad, precio_unitario, subtotal)
                    VALUES (%s, %s, %s, %s, %s)
                """, (id_venta, producto, cantidad, precio, subtotal))

            connection.commit()
            flash('Venta registrada exitosamente')
            return redirect(url_for('ventas'))
        except Exception as ex:
            print(ex)
            flash('Error al registrar la venta')
        finally:
            if connection:
                connection.close()

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id_producto, nombre, precio FROM productos")
        productos = cursor.fetchall()
    except Exception as ex:
        print(ex)
        productos = []
    finally:
        if connection:
            connection.close()

    return render_template('nueva_venta.html', productos=productos)



# Manejo de errores
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


if __name__ == '__main__':
    csrf.init_app(app)
    app.run(debug=True)
