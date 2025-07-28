"""
Database migration to create WhatsApp integration tables.
Run this to set up the WhatsApp database schema.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from src.core.database import get_db_engine
from src.models.whatsapp import (
    WhatsAppContact, WhatsAppConversation, WhatsAppMessage, WhatsAppWebhookEvent
)

async def create_whatsapp_tables():
    """Create WhatsApp integration tables."""
    
    engine = get_db_engine()
    
    # SQL for creating WhatsApp tables with proper indexes and constraints
    whatsapp_tables_sql = """
    -- WhatsApp Contacts Table
    CREATE TABLE IF NOT EXISTS whatsapp_contacts (
        id VARCHAR(36) PRIMARY KEY,
        tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        phone_number VARCHAR(20) NOT NULL,
        whatsapp_id VARCHAR(100) NOT NULL,
        profile_name VARCHAR(255),
        first_name VARCHAR(100),
        last_name VARCHAR(100),
        email VARCHAR(255),
        language_code VARCHAR(10) DEFAULT 'fr',
        timezone VARCHAR(50),
        opt_in_status BOOLEAN DEFAULT true,
        blocked BOOLEAN DEFAULT false,
        tags JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_seen TIMESTAMP
    );

    -- WhatsApp Conversations Table
    CREATE TABLE IF NOT EXISTS whatsapp_conversations (
        id VARCHAR(36) PRIMARY KEY,
        tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        contact_id VARCHAR(36) NOT NULL REFERENCES whatsapp_contacts(id) ON DELETE CASCADE,
        assigned_agent_id INTEGER REFERENCES agents(id) ON DELETE SET NULL,
        status VARCHAR(20) DEFAULT 'active',
        subject VARCHAR(255),
        priority VARCHAR(20) DEFAULT 'normal',
        orchestrator_conversation_id VARCHAR(36),
        last_agent_response TIMESTAMP,
        auto_response_enabled BOOLEAN DEFAULT true,
        business_hours_only BOOLEAN DEFAULT false,
        escalation_rules JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        closed_at TIMESTAMP
    );

    -- WhatsApp Messages Table
    CREATE TABLE IF NOT EXISTS whatsapp_messages (
        id VARCHAR(36) PRIMARY KEY,
        tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        conversation_id VARCHAR(36) NOT NULL REFERENCES whatsapp_conversations(id) ON DELETE CASCADE,
        contact_id VARCHAR(36) NOT NULL REFERENCES whatsapp_contacts(id) ON DELETE CASCADE,
        whatsapp_message_id VARCHAR(100) UNIQUE,
        message_type VARCHAR(20) DEFAULT 'text',
        direction VARCHAR(10) NOT NULL,
        content TEXT,
        media_url VARCHAR(500),
        media_type VARCHAR(50),
        media_size INTEGER,
        status VARCHAR(20) DEFAULT 'pending',
        delivered_at TIMESTAMP,
        read_at TIMESTAMP,
        failed_reason VARCHAR(255),
        processed_by_agent_id INTEGER REFERENCES agents(id) ON DELETE SET NULL,
        orchestrator_message_id VARCHAR(36),
        auto_generated BOOLEAN DEFAULT false,
        template_name VARCHAR(100),
        template_language VARCHAR(10),
        interactive_data JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- WhatsApp Webhook Events Table
    CREATE TABLE IF NOT EXISTS whatsapp_webhook_events (
        id VARCHAR(36) PRIMARY KEY,
        tenant_id VARCHAR(36) REFERENCES tenants(id) ON DELETE CASCADE,
        event_type VARCHAR(50) NOT NULL,
        webhook_payload JSONB NOT NULL,
        processed BOOLEAN DEFAULT false,
        processing_error TEXT,
        message_id VARCHAR(36) REFERENCES whatsapp_messages(id) ON DELETE SET NULL,
        conversation_id VARCHAR(36) REFERENCES whatsapp_conversations(id) ON DELETE SET NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed_at TIMESTAMP
    );

    -- Indexes for WhatsApp Contacts
    CREATE INDEX IF NOT EXISTS idx_whatsapp_contacts_tenant_phone 
        ON whatsapp_contacts(tenant_id, phone_number);
    CREATE UNIQUE INDEX IF NOT EXISTS idx_whatsapp_contacts_tenant_phone_unique 
        ON whatsapp_contacts(tenant_id, phone_number);
    CREATE UNIQUE INDEX IF NOT EXISTS idx_whatsapp_contacts_tenant_whatsapp_id_unique 
        ON whatsapp_contacts(tenant_id, whatsapp_id);
    CREATE INDEX IF NOT EXISTS idx_whatsapp_contacts_opt_in 
        ON whatsapp_contacts(tenant_id, opt_in_status);
    CREATE INDEX IF NOT EXISTS idx_whatsapp_contacts_created_at 
        ON whatsapp_contacts(created_at);

    -- Indexes for WhatsApp Conversations
    CREATE INDEX IF NOT EXISTS idx_whatsapp_conversations_tenant_contact 
        ON whatsapp_conversations(tenant_id, contact_id);
    CREATE INDEX IF NOT EXISTS idx_whatsapp_conversations_tenant_agent 
        ON whatsapp_conversations(tenant_id, assigned_agent_id);
    CREATE INDEX IF NOT EXISTS idx_whatsapp_conversations_status 
        ON whatsapp_conversations(tenant_id, status);
    CREATE INDEX IF NOT EXISTS idx_whatsapp_conversations_created_at 
        ON whatsapp_conversations(created_at);

    -- Indexes for WhatsApp Messages
    CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_tenant_conversation 
        ON whatsapp_messages(tenant_id, conversation_id);
    CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_tenant_contact 
        ON whatsapp_messages(tenant_id, contact_id);
    CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_direction_status 
        ON whatsapp_messages(direction, status);
    CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_created_at 
        ON whatsapp_messages(created_at);
    CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_whatsapp_id 
        ON whatsapp_messages(whatsapp_message_id);

    -- Indexes for WhatsApp Webhook Events
    CREATE INDEX IF NOT EXISTS idx_whatsapp_webhook_events_tenant_type 
        ON whatsapp_webhook_events(tenant_id, event_type);
    CREATE INDEX IF NOT EXISTS idx_whatsapp_webhook_events_processed 
        ON whatsapp_webhook_events(processed);
    CREATE INDEX IF NOT EXISTS idx_whatsapp_webhook_events_created_at 
        ON whatsapp_webhook_events(created_at);

    -- Triggers for updated_at timestamps
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ language 'plpgsql';

    -- Apply triggers to WhatsApp tables
    DROP TRIGGER IF EXISTS update_whatsapp_contacts_updated_at ON whatsapp_contacts;
    CREATE TRIGGER update_whatsapp_contacts_updated_at 
        BEFORE UPDATE ON whatsapp_contacts 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

    DROP TRIGGER IF EXISTS update_whatsapp_conversations_updated_at ON whatsapp_conversations;
    CREATE TRIGGER update_whatsapp_conversations_updated_at 
        BEFORE UPDATE ON whatsapp_conversations 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

    DROP TRIGGER IF EXISTS update_whatsapp_messages_updated_at ON whatsapp_messages;
    CREATE TRIGGER update_whatsapp_messages_updated_at 
        BEFORE UPDATE ON whatsapp_messages 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

    -- Row Level Security (RLS) for multi-tenant isolation
    ALTER TABLE whatsapp_contacts ENABLE ROW LEVEL SECURITY;
    ALTER TABLE whatsapp_conversations ENABLE ROW LEVEL SECURITY;
    ALTER TABLE whatsapp_messages ENABLE ROW LEVEL SECURITY;
    ALTER TABLE whatsapp_webhook_events ENABLE ROW LEVEL SECURITY;

    -- RLS Policies for WhatsApp Contacts
    DROP POLICY IF EXISTS whatsapp_contacts_tenant_isolation ON whatsapp_contacts;
    CREATE POLICY whatsapp_contacts_tenant_isolation ON whatsapp_contacts
        USING (tenant_id = current_setting('app.current_tenant_id', true));

    -- RLS Policies for WhatsApp Conversations
    DROP POLICY IF EXISTS whatsapp_conversations_tenant_isolation ON whatsapp_conversations;
    CREATE POLICY whatsapp_conversations_tenant_isolation ON whatsapp_conversations
        USING (tenant_id = current_setting('app.current_tenant_id', true));

    -- RLS Policies for WhatsApp Messages
    DROP POLICY IF EXISTS whatsapp_messages_tenant_isolation ON whatsapp_messages;
    CREATE POLICY whatsapp_messages_tenant_isolation ON whatsapp_messages
        USING (tenant_id = current_setting('app.current_tenant_id', true));

    -- RLS Policies for WhatsApp Webhook Events
    DROP POLICY IF EXISTS whatsapp_webhook_events_tenant_isolation ON whatsapp_webhook_events;
    CREATE POLICY whatsapp_webhook_events_tenant_isolation ON whatsapp_webhook_events
        USING (tenant_id = current_setting('app.current_tenant_id', true) OR tenant_id IS NULL);
    """

    try:
        async with engine.begin() as conn:
            print("Creating WhatsApp integration tables...")
            
            # Execute the SQL
            await conn.execute(text(whatsapp_tables_sql))
            
            print("✅ WhatsApp tables created successfully!")
            print("\nCreated tables:")
            print("- whatsapp_contacts")
            print("- whatsapp_conversations") 
            print("- whatsapp_messages")
            print("- whatsapp_webhook_events")
            print("\nCreated indexes and constraints for optimal performance")
            print("Created RLS policies for multi-tenant isolation")
            
    except Exception as e:
        print(f"❌ Error creating WhatsApp tables: {e}")
        raise
    finally:
        await engine.dispose()


async def verify_whatsapp_tables():
    """Verify that WhatsApp tables were created correctly."""
    
    engine = get_db_engine()
    
    verification_sql = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE 'whatsapp_%'
    ORDER BY table_name;
    """
    
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text(verification_sql))
            tables = [row[0] for row in result.fetchall()]
            
            expected_tables = [
                'whatsapp_contacts',
                'whatsapp_conversations', 
                'whatsapp_messages',
                'whatsapp_webhook_events'
            ]
            
            print("\n🔍 Verifying WhatsApp tables...")
            
            for table in expected_tables:
                if table in tables:
                    print(f"✅ {table} - Created")
                else:
                    print(f"❌ {table} - Missing")
            
            if set(expected_tables).issubset(set(tables)):
                print("\n✅ All WhatsApp tables verified successfully!")
                return True
            else:
                print("\n❌ Some WhatsApp tables are missing!")
                return False
                
    except Exception as e:
        print(f"❌ Error verifying WhatsApp tables: {e}")
        return False
    finally:
        await engine.dispose()


async def main():
    """Main function to create and verify WhatsApp tables."""
    print("🚀 WhatsApp Integration Database Setup")
    print("=" * 50)
    
    try:
        # Create tables
        await create_whatsapp_tables()
        
        # Verify tables
        success = await verify_whatsapp_tables()
        
        if success:
            print("\n🎉 WhatsApp integration database setup completed successfully!")
            print("\nNext steps:")
            print("1. Configure WhatsApp environment variables in .env")
            print("2. Set up WhatsApp Business API webhook")
            print("3. Test the integration")
        else:
            print("\n❌ WhatsApp integration database setup failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
