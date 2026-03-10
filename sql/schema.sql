-- Drop view si existe para no tener conflictos al recrear tablas
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

-- Tabla: jugadores
CREATE TABLE IF NOT EXISTS jugadores (
    id VARCHAR(36) PRIMARY KEY,
    equipo_id VARCHAR(36),
    nombre VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipo_id) REFERENCES equipos(id)
);

-- Tabla: cuerpo_tecnico
CREATE TABLE IF NOT EXISTS cuerpo_tecnico (
    id VARCHAR(36) PRIMARY KEY,
    equipo_id VARCHAR(36),
    nombre VARCHAR(100) NOT NULL,
    rol VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipo_id) REFERENCES equipos(id)
);

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

-- Tabla: eventos
-- Representa las acciones dentro de un partido (goles, tarjetas, faltas, tiros, etc.)
CREATE TABLE IF NOT EXISTS eventos (
    id VARCHAR(36) PRIMARY KEY,
    partido_id VARCHAR(36) NOT NULL,
    equipo_id VARCHAR(36),
    jugador_id VARCHAR(36),
    tipo_evento VARCHAR(50) NOT NULL, -- ej: 'GOL', 'TARJETA_AMARILLA', 'FALTA', 'TIRO_PUERTA'
    minuto INT NOT NULL,
    segundo INT,
    periodo VARCHAR(20), -- ej: '1T', '2T', 'PR1', 'PR2'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (partido_id) REFERENCES partidos(id),
    FOREIGN KEY (equipo_id) REFERENCES equipos(id),
    FOREIGN KEY (jugador_id) REFERENCES jugadores(id)
);


-- Vista Desnormalizada para Looker Studio
-- Une todas las tablas para permitir análisis sin hacer JOINs en Looker
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
    
    -- Equipo involucrado en el evento
    eq.id AS equipo_evento_id,
    eq.nombre AS equipo_evento_nombre,
    
    -- Jugador involucrado en el evento
    j.id AS jugador_id,
    j.nombre AS jugador_nombre,
    
    -- Contexto del partido
    el.id AS equipo_local_id,
    el.nombre AS equipo_local_nombre,
    ev.id AS equipo_visitante_id,
    ev.nombre AS equipo_visitante_nombre

FROM eventos e
LEFT JOIN partidos p ON e.partido_id = p.id
LEFT JOIN torneos t ON p.torneo_id = t.id
LEFT JOIN equipos eq ON e.equipo_id = eq.id
LEFT JOIN jugadores j ON e.jugador_id = j.id
LEFT JOIN equipos el ON p.equipo_local_id = el.id
LEFT JOIN equipos ev ON p.equipo_visitante_id = ev.id;
