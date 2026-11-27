-- =====================================================================
-- ChainSight — Database schema (MySQL 8)
-- Phase 2: the simulated Warsaw electronics manufacturer
--
-- Re-runnable: drops and recreates all tables.
-- All company data loaded into these tables is SIMULATED.
-- =====================================================================

USE chainsight;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS event_nodes;
DROP TABLE IF EXISTS risk_events;
DROP TABLE IF EXISTS shipments;
DROP TABLE IF EXISTS purchase_orders;
DROP TABLE IF EXISTS inventory;
DROP TABLE IF EXISTS supplier_materials;
DROP TABLE IF EXISTS route_legs;
DROP TABLE IF EXISTS routes;
DROP TABLE IF EXISTS nodes;
DROP TABLE IF EXISTS materials;
DROP TABLE IF EXISTS suppliers;
SET FOREIGN_KEY_CHECKS = 1;


-- ---------------------------------------------------------------------
-- 1. SUPPLIERS — who we buy from
-- ---------------------------------------------------------------------
CREATE TABLE suppliers (
    supplier_id        VARCHAR(10)   PRIMARY KEY,          -- e.g. SUP001
    supplier_name      VARCHAR(100)  NOT NULL,
    country            VARCHAR(60)   NOT NULL,
    country_code       CHAR(3)       NOT NULL,             -- ISO-3, e.g. CHN, TWN, DEU
    city               VARCHAR(60),
    latitude           DECIMAL(8,5),
    longitude          DECIMAL(8,5),
    reliability_score  DECIMAL(3,2)  CHECK (reliability_score BETWEEN 0 AND 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ---------------------------------------------------------------------
-- 2. MATERIALS — what we buy
-- criticality: A = production stops without it, B = important, C = minor
-- ---------------------------------------------------------------------
CREATE TABLE materials (
    material_id     VARCHAR(10)   PRIMARY KEY,             -- e.g. MAT001
    material_name   VARCHAR(100)  NOT NULL,
    category        VARCHAR(50)   NOT NULL,                -- Semiconductors, PCBs, Metal parts...
    criticality     ENUM('A','B','C') NOT NULL,
    unit            VARCHAR(20)   NOT NULL DEFAULT 'pcs',
    unit_cost_eur   DECIMAL(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ---------------------------------------------------------------------
-- 3. SUPPLIER_MATERIALS — which supplier provides which material
-- A material with only one row here is SINGLE-SOURCED (a vulnerability).
-- ---------------------------------------------------------------------
CREATE TABLE supplier_materials (
    supplier_id      VARCHAR(10)  NOT NULL,
    material_id      VARCHAR(10)  NOT NULL,
    is_primary       BOOLEAN      NOT NULL DEFAULT TRUE,
    lead_time_days   INT          NOT NULL,                -- order to delivery, normal conditions
    price_eur        DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (supplier_id, material_id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    FOREIGN KEY (material_id) REFERENCES materials(material_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ---------------------------------------------------------------------
-- 4. NODES — places on the map that goods pass through
-- Ports, maritime chokepoints (Suez, Bab-el-Mandeb...), rail hubs, borders.
-- Risk events are linked to these, which is how we detect exposure.
-- ---------------------------------------------------------------------
CREATE TABLE nodes (
    node_id        VARCHAR(20)   PRIMARY KEY,              -- e.g. PORT_SHA, CP_SUEZ
    node_name      VARCHAR(100)  NOT NULL,
    node_type      ENUM('port','chokepoint','rail_hub','border','factory') NOT NULL,
    country_code   CHAR(3),                                -- NULL for open-sea chokepoints
    latitude       DECIMAL(8,5),
    longitude      DECIMAL(8,5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ---------------------------------------------------------------------
-- 5. ROUTES — a named way of getting goods from A to B
-- ---------------------------------------------------------------------
CREATE TABLE routes (
    route_id              VARCHAR(20)  PRIMARY KEY,        -- e.g. R_SHA_GDN_SUEZ
    route_name            VARCHAR(100) NOT NULL,
    transport_mode        ENUM('sea','rail','road','air','multimodal') NOT NULL,
    origin_node_id        VARCHAR(20)  NOT NULL,
    destination_node_id   VARCHAR(20)  NOT NULL,
    typical_transit_days  INT          NOT NULL,
    FOREIGN KEY (origin_node_id)      REFERENCES nodes(node_id),
    FOREIGN KEY (destination_node_id) REFERENCES nodes(node_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ---------------------------------------------------------------------
-- 6. ROUTE_LEGS — each route broken into ordered steps
-- e.g. Shanghai -> Malacca -> Bab-el-Mandeb -> Suez -> Gdansk
-- ---------------------------------------------------------------------
CREATE TABLE route_legs (
    route_id      VARCHAR(20) NOT NULL,
    leg_seq       INT         NOT NULL,                    -- 1, 2, 3...
    from_node_id  VARCHAR(20) NOT NULL,
    to_node_id    VARCHAR(20) NOT NULL,
    transit_days  INT         NOT NULL,
    PRIMARY KEY (route_id, leg_seq),
    FOREIGN KEY (route_id)     REFERENCES routes(route_id),
    FOREIGN KEY (from_node_id) REFERENCES nodes(node_id),
    FOREIGN KEY (to_node_id)   REFERENCES nodes(node_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ---------------------------------------------------------------------
-- 7. INVENTORY — how much we have and how fast we use it
-- stock coverage (days) = on_hand_qty / avg_daily_consumption
-- ---------------------------------------------------------------------
CREATE TABLE inventory (
    material_id            VARCHAR(10)   PRIMARY KEY,
    snapshot_date          DATE          NOT NULL,
    on_hand_qty            INT           NOT NULL,
    safety_stock_qty       INT           NOT NULL DEFAULT 0,
    avg_daily_consumption  DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (material_id) REFERENCES materials(material_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ---------------------------------------------------------------------
-- 8. PURCHASE_ORDERS — what we have ordered
-- ---------------------------------------------------------------------
CREATE TABLE purchase_orders (
    po_id                   VARCHAR(12)   PRIMARY KEY,     -- e.g. PO000123
    supplier_id             VARCHAR(10)   NOT NULL,
    material_id             VARCHAR(10)   NOT NULL,
    order_date              DATE          NOT NULL,
    quantity                INT           NOT NULL,
    unit_price_eur          DECIMAL(10,2) NOT NULL,
    expected_delivery_date  DATE          NOT NULL,
    status                  ENUM('open','in_transit','delivered','cancelled') NOT NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    FOREIGN KEY (material_id) REFERENCES materials(material_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ---------------------------------------------------------------------
-- 9. SHIPMENTS — physical movement of a purchase order along a route
-- ---------------------------------------------------------------------
CREATE TABLE shipments (
    shipment_id      VARCHAR(12)  PRIMARY KEY,             -- e.g. SHP000123
    po_id            VARCHAR(12)  NOT NULL,
    route_id         VARCHAR(20)  NOT NULL,
    departure_date   DATE,
    eta_date         DATE         NOT NULL,                -- estimated arrival in Warsaw
    current_leg_seq  INT,                                  -- where the shipment is now
    status           ENUM('planned','in_transit','delayed','arrived') NOT NULL,
    FOREIGN KEY (po_id)    REFERENCES purchase_orders(po_id),
    FOREIGN KEY (route_id) REFERENCES routes(route_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ---------------------------------------------------------------------
-- 10. RISK_EVENTS — real-world disruptions (filled in Phase 3)
-- likelihood / severity on 1–5 scale; confidence 0–1 kept separate,
-- so an uncertain news report doesn't become a high-confidence alert.
-- ---------------------------------------------------------------------
CREATE TABLE risk_events (
    event_id                 INT AUTO_INCREMENT PRIMARY KEY,
    source                   VARCHAR(30)   NOT NULL,       -- GDELT, GDACS, PORTWATCH, MANUAL
    source_event_id          VARCHAR(100),                 -- ID in the original source
    event_type               ENUM('conflict','weather','port_congestion','canal_restriction',
                                  'sanction','trade_policy','supplier_failure','other') NOT NULL,
    title                    VARCHAR(255)  NOT NULL,
    description              TEXT,
    country_code             CHAR(3),
    latitude                 DECIMAL(8,5),
    longitude                DECIMAL(8,5),
    likelihood               TINYINT       CHECK (likelihood BETWEEN 1 AND 5),
    severity                 TINYINT       CHECK (severity BETWEEN 1 AND 5),
    confidence               DECIMAL(3,2)  CHECK (confidence BETWEEN 0 AND 1),
    start_date               DATE          NOT NULL,
    expected_duration_days   INT,
    source_url               VARCHAR(500),
    ingested_at              TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ---------------------------------------------------------------------
-- 11. EVENT_NODES — which ports/chokepoints an event affects
-- This link is what lets one SQL join answer:
--   "which of our shipments pass through a place with an active event?"
-- ---------------------------------------------------------------------
CREATE TABLE event_nodes (
    event_id  INT          NOT NULL,
    node_id   VARCHAR(20)  NOT NULL,
    PRIMARY KEY (event_id, node_id),
    FOREIGN KEY (event_id) REFERENCES risk_events(event_id),
    FOREIGN KEY (node_id)  REFERENCES nodes(node_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
