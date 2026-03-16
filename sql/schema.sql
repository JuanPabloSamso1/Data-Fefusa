-- Limpieza de vistas para evitar conflictos en recreaciones
DROP VIEW IF EXISTS vw_looker_eventos;

-- Tabla: torneos
CREATE TABLE IF NOT EXISTS torneos (
    id VARCHAR(36) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    temporada VARCHAR(100) NOT NULL,
    pais VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: equipos
CREATE TABLE IF NOT EXISTS equipos (
    id VARCHAR(36) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla unificada: personas
CREATE TABLE IF NOT EXISTS personas (
    id VARCHAR(36) PRIMARY KEY,
    equipo_id VARCHAR(36),
    nombre VARCHAR(100) NOT NULL,
    tipo_persona ENUM('JUGADOR', 'CT') NOT NULL,
    rol_ct VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipo_id) REFERENCES equipos(id)
);

-- Tablas legacy para transición/migración de consumidores históricos
CREATE TABLE IF NOT EXISTS jugadores (
    id VARCHAR(36) PRIMARY KEY,
    equipo_id VARCHAR(36),
    nombre VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipo_id) REFERENCES equipos(id)
);

CREATE TABLE IF NOT EXISTS cuerpo_tecnico (
    id VARCHAR(36) PRIMARY KEY,
    equipo_id VARCHAR(36),
    nombre VARCHAR(100) NOT NULL,
    rol VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipo_id) REFERENCES equipos(id)
);

-- Migración de datos existentes -> personas
INSERT INTO personas (id, equipo_id, nombre, tipo_persona, rol_ct)
SELECT j.id, j.equipo_id, j.nombre, 'JUGADOR', NULL
FROM jugadores j
ON DUPLICATE KEY UPDATE
    equipo_id = VALUES(equipo_id),
    nombre = VALUES(nombre),
    tipo_persona = VALUES(tipo_persona),
    rol_ct = VALUES(rol_ct);

INSERT INTO personas (id, equipo_id, nombre, tipo_persona, rol_ct)
SELECT ct.id, ct.equipo_id, ct.nombre, 'CT', ct.rol
FROM cuerpo_tecnico ct
ON DUPLICATE KEY UPDATE
    equipo_id = VALUES(equipo_id),
    nombre = VALUES(nombre),
    tipo_persona = VALUES(tipo_persona),
    rol_ct = VALUES(rol_ct);

-- Reemplazo de tablas legacy por vistas de compatibilidad
DROP TABLE IF EXISTS jugadores;
DROP TABLE IF EXISTS cuerpo_tecnico;

CREATE VIEW jugadores AS
SELECT
    id,
    equipo_id,
    nombre,
    created_at
FROM personas
WHERE tipo_persona = 'JUGADOR';

CREATE VIEW cuerpo_tecnico AS
SELECT
    id,
    equipo_id,
    nombre,
    rol_ct AS rol,
    created_at
FROM personas
WHERE tipo_persona = 'CT';

-- Tabla: partidos
CREATE TABLE IF NOT EXISTS partidos (
    id VARCHAR(36) PRIMARY KEY,
    torneo_id VARCHAR(36) NOT NULL,
    equipo_local_id VARCHAR(36) NOT NULL,
    equipo_visitante_id VARCHAR(36) NOT NULL,
    fecha DATETIME NOT NULL,
    jornada INT,
    goles_local INT DEFAULT 0,
    goles_visitante INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (torneo_id) REFERENCES torneos(id),
    FOREIGN KEY (equipo_local_id) REFERENCES equipos(id),
    FOREIGN KEY (equipo_visitante_id) REFERENCES equipos(id)
);

-- Tabla: eventos (persona_id reemplaza jugador_id)
CREATE TABLE IF NOT EXISTS eventos (
    id VARCHAR(36) PRIMARY KEY,
    partido_id VARCHAR(36) NOT NULL,
    equipo_id VARCHAR(36),
    persona_id VARCHAR(36),
    tipo_evento VARCHAR(50) NOT NULL,
    minuto INT NOT NULL,
    segundo INT,
    periodo VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (partido_id) REFERENCES partidos(id),
    FOREIGN KEY (equipo_id) REFERENCES equipos(id),
    FOREIGN KEY (persona_id) REFERENCES personas(id)
);

-- Vista desnormalizada para Looker Studio
CREATE VIEW vw_looker_eventos AS
SELECT
    e.id AS evento_id,
    e.tipo_evento,
    e.minuto,
    e.segundo,
    e.periodo,

    p.id AS partido_id,
    p.fecha AS partido_fecha,
    p.jornada AS partido_jornada,
    p.goles_local,
    p.goles_visitante,

    t.id AS torneo_id,
    t.nombre AS torneo_nombre,
    t.temporada AS torneo_temporada,

    eq.id AS equipo_evento_id,
    eq.nombre AS equipo_evento_nombre,

    pe.id AS persona_id,
    pe.nombre AS persona_nombre,
    pe.tipo_persona,
    pe.rol_ct,

    -- Alias legacy para consumidores antiguos
    pe.id AS jugador_id,
    pe.nombre AS jugador_nombre,

    el.id AS equipo_local_id,
    el.nombre AS equipo_local_nombre,
    ev.id AS equipo_visitante_id,
    ev.nombre AS equipo_visitante_nombre
FROM eventos e
LEFT JOIN partidos p ON e.partido_id = p.id
LEFT JOIN torneos t ON p.torneo_id = t.id
LEFT JOIN equipos eq ON e.equipo_id = eq.id
LEFT JOIN personas pe ON e.persona_id = pe.id
LEFT JOIN equipos el ON p.equipo_local_id = el.id
LEFT JOIN equipos ev ON p.equipo_visitante_id = ev.id;
