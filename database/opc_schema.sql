-- Multi-Agent Orchestration schema for a One Person Company (OPC)
-- PostgreSQL DDL, normalized to 3NF with explicit governance/audit entities.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE contract_status AS ENUM (
    'draft',
    'active',
    'paused',
    'completed',
    'terminated'
);

CREATE TYPE order_status AS ENUM (
    'draft',
    'confirmed',
    'fulfilled',
    'cancelled'
);

CREATE TYPE invoice_status AS ENUM (
    'draft',
    'issued',
    'paid',
    'overdue',
    'void'
);

CREATE TYPE bank_txn_status AS ENUM (
    'pending',
    'posted',
    'held',
    'released',
    'rejected'
);

CREATE TYPE risk_severity AS ENUM (
    'low',
    'medium',
    'high',
    'critical'
);

CREATE TYPE decision_status AS ENUM (
    'auto_approved',
    'pending_founder_approval',
    'approved',
    'rejected',
    'expired'
);

CREATE TABLE customer (
    customer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_name TEXT NOT NULL,
    tax_id TEXT UNIQUE,
    payment_reliability NUMERIC(5,2) NOT NULL DEFAULT 0
        CHECK (payment_reliability >= 0 AND payment_reliability <= 100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE contract (
    contract_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customer(customer_id),
    contract_number TEXT NOT NULL UNIQUE,
    status contract_status NOT NULL DEFAULT 'draft',
    contract_value_vnd NUMERIC(18,2) NOT NULL CHECK (contract_value_vnd >= 0),
    start_date DATE NOT NULL,
    end_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (end_date IS NULL OR end_date >= start_date)
);

-- Bridge exists only to enforce that an order's customer matches its contract's customer.
CREATE TABLE contract_customer_bridge (
    contract_id UUID NOT NULL REFERENCES contract(contract_id),
    customer_id UUID NOT NULL REFERENCES customer(customer_id),
    PRIMARY KEY (contract_id, customer_id)
);

CREATE UNIQUE INDEX contract_customer_bridge_contract_uq
    ON contract_customer_bridge(contract_id);

CREATE OR REPLACE FUNCTION sync_contract_customer_bridge()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO contract_customer_bridge (contract_id, customer_id)
    VALUES (NEW.contract_id, NEW.customer_id)
    ON CONFLICT (contract_id) DO UPDATE
    SET customer_id = EXCLUDED.customer_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_contract_customer_bridge
AFTER INSERT OR UPDATE OF customer_id ON contract
FOR EACH ROW
EXECUTE FUNCTION sync_contract_customer_bridge();

CREATE TABLE opc_order (
    order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id UUID NOT NULL REFERENCES contract(contract_id),
    customer_id UUID NOT NULL REFERENCES customer(customer_id),
    order_number TEXT NOT NULL UNIQUE,
    status order_status NOT NULL DEFAULT 'draft',
    revenue NUMERIC(18,2) NOT NULL CHECK (revenue >= 0),
    cost NUMERIC(18,2) NOT NULL CHECK (cost >= 0),
    margin NUMERIC(10,6) GENERATED ALWAYS AS (
        CASE
            WHEN revenue = 0 THEN NULL
            ELSE (revenue - cost) / revenue
        END
    ) STORED,
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT opc_order_customer_contract_fk
        FOREIGN KEY (contract_id, customer_id)
        REFERENCES contract_customer_bridge(contract_id, customer_id)
);

CREATE TABLE invoice (
    invoice_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES opc_order(order_id),
    customer_id UUID NOT NULL REFERENCES customer(customer_id),
    invoice_number TEXT NOT NULL UNIQUE,
    status invoice_status NOT NULL DEFAULT 'draft',
    amount_vnd NUMERIC(18,2) NOT NULL CHECK (amount_vnd >= 0),
    issued_date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL,
    paid_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (due_date >= issued_date),
    CHECK (paid_date IS NULL OR paid_date >= issued_date)
);

CREATE TABLE bank_transaction (
    txn_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customer(customer_id),
    invoice_id UUID REFERENCES invoice(invoice_id),
    bank_account_ref TEXT NOT NULL,
    txn_reference TEXT NOT NULL UNIQUE,
    txn_timestamp TIMESTAMPTZ NOT NULL,
    amount_vnd NUMERIC(18,2) NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('inflow', 'outflow')),
    status bank_txn_status NOT NULL DEFAULT 'pending',
    transaction_risk_score NUMERIC(5,2) NOT NULL DEFAULT 0
        CHECK (transaction_risk_score >= 0 AND transaction_risk_score <= 100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE cashflow (
    cashflow_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    projection_date DATE NOT NULL,
    opening_cash_vnd NUMERIC(18,2) NOT NULL,
    projected_inflows_vnd NUMERIC(18,2) NOT NULL DEFAULT 0,
    projected_outflows_vnd NUMERIC(18,2) NOT NULL DEFAULT 0,
    projected_closing_cash NUMERIC(18,2) NOT NULL,
    generated_by_agent TEXT NOT NULL DEFAULT 'data_finance_agent',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (projection_date, generated_by_agent)
);

CREATE TABLE opc_risk_log (
    risk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_code TEXT NOT NULL,
    severity risk_severity NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id UUID,
    alert_message TEXT NOT NULL,
    audit_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    requires_founder_approval BOOLEAN NOT NULL DEFAULT false,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE decision (
    decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_code TEXT,
    entity_type TEXT NOT NULL,
    entity_id UUID,
    recommendation TEXT NOT NULL,
    decision_amount_vnd NUMERIC(18,2) CHECK (decision_amount_vnd IS NULL OR decision_amount_vnd >= 0),
    risk_level risk_severity NOT NULL DEFAULT 'low',
    status decision_status NOT NULL DEFAULT 'pending_founder_approval',
    founder_approved_by TEXT,
    founder_approved_at TIMESTAMPTZ,
    rationale JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (
        (status IN ('approved', 'rejected') AND founder_approved_by IS NOT NULL)
        OR status NOT IN ('approved', 'rejected')
    )
);

CREATE INDEX idx_contract_customer_id ON contract(customer_id);
CREATE INDEX idx_order_contract_customer ON opc_order(contract_id, customer_id);
CREATE INDEX idx_invoice_order_customer ON invoice(order_id, customer_id);
CREATE INDEX idx_bank_txn_risk_score ON bank_transaction(transaction_risk_score);
CREATE INDEX idx_cashflow_projection_date ON cashflow(projection_date);
CREATE INDEX idx_risk_rule_created ON opc_risk_log(rule_code, created_at DESC);
CREATE INDEX idx_decision_status_created ON decision(status, created_at DESC);
