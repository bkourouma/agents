# WhatsApp Business API Integration Guide

## Overview

This guide provides step-by-step instructions for integrating WhatsApp Business API with your AI Agent Platform. The integration allows users to interact with your AI agents directly through WhatsApp messages.

## Prerequisites

### 1. WhatsApp Business Account Requirements
- **Business Phone Number**: A dedicated phone number for WhatsApp Business
- **Meta Business Manager Account**: Required for WhatsApp Business API access
- **Verified Business**: Your business must be verified with Meta
- **HTTPS Domain**: Your webhook endpoint must use HTTPS (Azure Web Apps provides this)

### 2. Technical Requirements
- **Public Webhook URL**: `https://your-domain.azurewebsites.net/api/v1/whatsapp/webhook`
- **Database**: PostgreSQL with WhatsApp tables (automatically created)
- **Environment Variables**: WhatsApp API credentials

## Step-by-Step Setup

### Step 1: Meta Business Manager Setup

1. **Create Meta Business Manager Account**
   - Go to [business.facebook.com](https://business.facebook.com)
   - Create a new business account or use existing one
   - Verify your business information

2. **Add WhatsApp Business Account**
   - In Business Manager, go to "WhatsApp" → "Get Started"
   - Create a new WhatsApp Business Account
   - Add your business phone number
   - Verify the phone number via SMS/call

3. **Create Meta Developer App**
   - Go to [developers.facebook.com](https://developers.facebook.com)
   - Create a new app → "Business" type
   - Add WhatsApp product to your app
   - Connect your WhatsApp Business Account to the app

### Step 2: Get API Credentials

1. **Access Token**
   - In your Meta Developer App → WhatsApp → Getting Started
   - Generate a permanent access token
   - Copy the token (starts with `EAA...`)

2. **Phone Number ID**
   - In WhatsApp → Getting Started
   - Find your phone number and copy its ID (numeric)

3. **Business Account ID**
   - In WhatsApp → Getting Started
   - Copy the Business Account ID

4. **App Secret**
   - In App Settings → Basic
   - Copy the App Secret (for webhook signature verification)

5. **Webhook Verify Token**
   - Generate a secure random string (e.g., `my_secure_webhook_token_2024`)
   - You'll use this to verify webhook setup

### Step 3: Configure Environment Variables

1. **Copy Environment Template**
   ```bash
   cp .env.whatsapp.example .env.whatsapp
   ```

2. **Update Your .env File**
   ```env
   # Add these to your existing .env file
   WHATSAPP_ACCESS_TOKEN=your_permanent_access_token_here
   WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id_here
   WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id_here
   WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_secure_verify_token_here
   WHATSAPP_APP_SECRET=your_app_secret_here
   WHATSAPP_API_VERSION=v18.0
   ```

### Step 4: Deploy and Configure Webhook

1. **Deploy Your Application**
   - Ensure your application is deployed to Azure Web Apps
   - Verify the webhook endpoint is accessible: `https://your-domain.azurewebsites.net/api/v1/whatsapp/webhook`

2. **Configure Webhook in Meta Developer Console**
   - Go to WhatsApp → Configuration → Webhook
   - Set Callback URL: `https://your-domain.azurewebsites.net/api/v1/whatsapp/webhook`
   - Set Verify Token: (the token you generated in Step 2.5)
   - Click "Verify and Save"

3. **Subscribe to Webhook Fields**
   - Subscribe to these fields:
     - `messages` (required)
     - `message_deliveries` (recommended)
     - `message_reads` (recommended)
     - `message_echoes` (optional)

### Step 5: Test the Integration

1. **Check Integration Status**
   ```bash
   curl https://your-domain.azurewebsites.net/api/v1/whatsapp/status
   ```

2. **Send Test Message**
   - Send a WhatsApp message to your business number
   - Check the webhook events endpoint for processing logs
   - Verify the message appears in your database

3. **Test Agent Response**
   - Send a message that should trigger your orchestrator
   - Verify the agent responds via WhatsApp

## Database Schema

The integration automatically creates these tables:

- **whatsapp_contacts**: Contact information and preferences
- **whatsapp_conversations**: Conversation management and agent assignment
- **whatsapp_messages**: Message history and status tracking
- **whatsapp_webhook_events**: Webhook event logging for debugging

## API Endpoints

### Webhook Endpoints (No Authentication)
- `GET /api/v1/whatsapp/webhook` - Webhook verification
- `POST /api/v1/whatsapp/webhook` - Receive WhatsApp events

### Management Endpoints (Authenticated)
- `GET /api/v1/whatsapp/contacts` - List contacts
- `GET /api/v1/whatsapp/conversations` - List conversations
- `GET /api/v1/whatsapp/conversations/{id}/messages` - Get conversation messages
- `POST /api/v1/whatsapp/send-message` - Send message
- `POST /api/v1/whatsapp/send-proactive-message` - Send proactive message
- `GET /api/v1/whatsapp/webhook-events` - Debug webhook events
- `GET /api/v1/whatsapp/status` - Integration status

## Message Flow

1. **Incoming Message**
   - User sends WhatsApp message
   - Meta sends webhook to your endpoint
   - Webhook service processes and stores message
   - Message is sent to orchestrator for agent routing
   - Agent generates response
   - Response is sent back via WhatsApp API

2. **Outgoing Message**
   - Agent or user sends message via API
   - Message is sent through WhatsApp Business API
   - Delivery status is tracked via webhooks

## Rate Limits

WhatsApp Business API has strict rate limits:
- **80 messages per second**
- **1,000 messages per minute**
- **10,000 messages per day** (varies by tier)

The integration includes automatic rate limiting to prevent API errors.

## Message Templates

For proactive messaging (marketing, notifications), you must use approved message templates:

1. **Create Templates in Meta Business Manager**
   - Go to WhatsApp → Message Templates
   - Create templates for different use cases
   - Wait for approval (24-48 hours)

2. **Use Templates in Code**
   ```python
   await whatsapp_api_service.send_template_message(
       phone_number="+1234567890",
       template_name="welcome_message",
       language_code="fr",
       parameters=["John", "Doe"]
   )
   ```

## Troubleshooting

### Common Issues

1. **Webhook Verification Fails**
   - Check verify token matches exactly
   - Ensure endpoint is accessible via HTTPS
   - Verify no authentication required for webhook endpoints

2. **Messages Not Received**
   - Check webhook subscription fields
   - Verify webhook events in debug endpoint
   - Check application logs for errors

3. **Cannot Send Messages**
   - Verify access token is valid and permanent
   - Check phone number ID is correct
   - Ensure recipient has opted in to receive messages

4. **Rate Limit Errors**
   - Implement proper rate limiting
   - Use message queuing for high volume
   - Consider upgrading WhatsApp Business API tier

### Debug Endpoints

- `GET /api/v1/whatsapp/status` - Check configuration
- `GET /api/v1/whatsapp/webhook-events` - View webhook processing logs
- Check application logs for detailed error messages

## Security Considerations

1. **Webhook Signature Verification**
   - Always verify webhook signatures using app secret
   - Reject requests with invalid signatures

2. **Access Token Security**
   - Use permanent access tokens
   - Store securely in environment variables
   - Rotate tokens periodically

3. **Rate Limiting**
   - Implement proper rate limiting
   - Monitor for abuse patterns
   - Use queuing for high-volume scenarios

4. **Data Privacy**
   - Comply with WhatsApp Business Policy
   - Implement proper data retention policies
   - Respect user opt-out preferences

## Production Deployment

### Azure Web Apps Configuration

1. **Environment Variables**
   - Set all WhatsApp environment variables in Azure App Service Configuration
   - Use Azure Key Vault for sensitive values

2. **Scaling**
   - Configure auto-scaling for webhook processing
   - Use Azure Service Bus for message queuing if needed

3. **Monitoring**
   - Set up Application Insights monitoring
   - Create alerts for webhook failures
   - Monitor rate limit usage

### Business Verification

For production use, you'll need:
- **Business Verification**: Complete Meta business verification
- **WhatsApp Business API Access**: Apply for official API access
- **Higher Rate Limits**: Request increased limits based on usage

## Support and Resources

- **Meta Developer Documentation**: [developers.facebook.com/docs/whatsapp](https://developers.facebook.com/docs/whatsapp)
- **WhatsApp Business API**: [business.whatsapp.com](https://business.whatsapp.com)
- **Meta Business Help**: [business.facebook.com/help](https://business.facebook.com/help)

## Next Steps

After successful integration:
1. Create message templates for your use cases
2. Implement business hours logic
3. Add conversation analytics
4. Create WhatsApp-specific agent configurations
5. Implement advanced features like interactive messages
