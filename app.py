<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nueva Propiedad - Terra Zen CRM</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #0a0a0a, #1a1a1a);
            color: #f4f4f4;
            min-height: 100vh;
            margin: 0;
            padding: 0;
        }

        .crm-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #f4f4f4;
        }

        .crm-header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: #1a1a1a;
            border-radius: 16px;
            border: 1px solid #444;
        }

        .crm-header h1 {
            color: #ffd700;
        }

        form {
            background: #1a1a1a;
            border: 1px solid #444;
            border-radius: 12px;
            padding: 30px;
        }

        label {
            display: block;
            margin-bottom: 5px;
            color: #ffd700;
        }

        input, select, textarea {
            width: 100%;
            padding: 10px;
            margin-bottom: 15px;
            border-radius: 8px;
            border: 1px solid #555;
            background: #222;
            color: #fff;
        }

        button {
            background: linear-gradient(135deg, #ffd700, #ff6b00);
            color: #000;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        button:hover {
            background: linear-gradient(135deg, #ff6b00, #ffd700);
            transform: translateY(-2px);
        }

        .btn-secondary {
            background: transparent;
            color: #ffd700;
            padding: 10px 20px;
            border: 1px solid #ffd700;
            border-radius: 8px;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .btn-secondary:hover {
            background: #ffd700;
            color: #000;
        }

        .warning-box {
            background-color: #442;
            border: 1px solid #ff6b6b;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            color: #ffd2d2;
            text-align: center;
        }

        .warning-box a {
            color: #ffd700;
            text-decoration: underline;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="crm-container">
        <div class="crm-header">
            <h1><i class="fas fa-home"></i> Nueva Propiedad</h1>
            <p>Agrega una nueva propiedad al sistema</p>
        </div>

        {% if not propietarios %}
        <!-- ⚠️ Aviso cuando no hay propietarios -->
        <div class="warning-box">
            ⚠️ No se puede crear una propiedad sin tener al menos un propietario registrado.<br><br>
            <a href="/crm/propietarios/nuevo">➕ Agregar propietario ahora</a>
        </div>

        <script>
            document.addEventListener('DOMContentLoaded', function () {
                document.querySelectorAll('input, select, textarea, button[type="submit"]').forEach(function (el) {
                    el.disabled = true;
                    el.style.opacity = '0.6';
                    el.style.cursor = 'not-allowed';
                });
            });
        </script>
        {% endif %}

        <form method="POST" action="/crm/propiedades/nueva">
            <label for="titulo">Título de la Propiedad</label>
            <input type="text" id="titulo" name="titulo" placeholder="Ej: Casa en la playa" required>

            <label for="descripcion">Descripción</label>
            <textarea id="descripcion" name="descripcion" rows="4" placeholder="Detalles de la propiedad"></textarea>

            <label for="precio">Precio (USD)</label>
            <input type="number" id="precio" name="precio" placeholder="Ej: 120000" step="0.01" required>

            <label for="ubicacion">Ubicación</label>
            <input type="text" id="ubicacion" name="ubicacion" placeholder="Ej: Monterrico, Guatemala" required>

            <label for="propietario_id">Propietario</label>
            <select id="propietario_id" name="propietario_id" required>
                <option value="">Seleccionar propietario</option>
                {% for propietario in propietarios %}
                    <option value="{{ propietario.id }}">{{ propietario.nombre }}</option>
                {% endfor %}
            </select>

            <button type="submit">Guardar Propiedad</button>
        </form>

        <div style="text-align:center; margin-top:20px;">
            <a href="/crm" class="btn-secondary"><i class="fas fa-arrow-left"></i> Volver al Panel</a>
        </div>
    </div>
</body>
</html>
