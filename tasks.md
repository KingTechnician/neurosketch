# NeuroSketch - GitHub Projects Tasks

## Week 1

### Isaiah
- [x] Set up GitHub repository and project structure
- [x] Create development environment documentation
- [x] Initialize FastAPI backend framework

### Mihiretu
- [x] Set up Streamlit application
- [x] Implement basic streamlit_canvas functionality
- [x] Create session management UI prototype
    - This involves making some menu that shows available sessions and allows the user to join them - doesn't have to be functional, just a placeholder for now

Helpful links:
- [Streamlit documentation](https://docs.streamlit.io/en/stable/)
- [Streamlit Drawing Canvas](https://github.com/andfanilo/streamlit-drawable-canvas) (You could really just copy most of the code from their example)

### Skeez
- [x] Design Postgres database schema
    - Create a table for users, and a table for sessions
    - Sessions are for users logged in, sessions are for instances of drawing as a group
- [x] Create scripts for database initialization
- [x] Document entity relationships (Stretch Goal)


Helpful links:
- [Postgres data types](https://medium.com/yavar/postgresql-data-types-f63948e143b6)
- [Creating tables in Postgres](https://python.plainenglish.io/demystifying-database-interactions-with-psycopg3-a-practical-guide-54f60d268211)
- [Creating entity relationships](https://hasura.io/learn/database/postgresql/core-concepts/6-postgresql-relationships/)
- [This explains what foreign keys are and how they work](https://medium.com/the-table-sql-and-devtalk/how-to-use-a-foreign-key-referring-to-the-source-table-in-postgres-170cdb98f948)

## Week 2

### Isaiah
- [x] Implement server-side session management
    - [x] Private key stored locally, public key stored in server
    - [ ] server sends encrypted code to client, client decrypts and sends back
- [ ] Create communication protocol for frontend-backend
    - Module for REST requests to the backend
- [ ] Implement API endpoints for user sessions
    - Create endpoints for creating, joining, and listing sessions
- [ ] Begin LLM integration research and planning
### Mihiretu
- [ ] Implement canvas state synchronization (Blockers: Isaiah's work first)
- [ ] Test drawing functionality with multiple users

### Skeez
- [ ] Begin work on session listing functionality (Blockers: Isaiah's work first)
    - Create a page that lists all available sessions

## Week 3- Interim Presentation Week

### Isaiah
- [ ] Start worker node setup for AI processing

### Mihiretu
- [ ] Add color picker and brush customization
- [ ] Document current functionality

### Skeez
- [ ] Test current system integration

## Week 4

### Isaiah
- [ ] Complete LLM API integration
- [ ] Implement multithreading for AI request handling
- [ ] Develop queuing system for AI tasks

### Mihiretu
- [ ] Implement layer management system
- [ ] Create AI prompt input interface
- [ ] Begin real-time collaborative features

### Skeez
- [ ] Implement anonymous user tracking
- [ ] Test database performance

## Week 5

### Isaiah
- [ ] Complete system integration
- [ ] Implement distributed computing aspects
- [ ] Begin testing across multiple machines

### Mihiretu
- [ ] Polish frontend interface
- [ ] Implement real-time updates visualization
- [ ] Add visual feedback for AI processing

### Skeez
- [ ] Identify bugs from testing
- [ ] Complete user documentation
- [ ] Assist with load testing

## Week 6 - Final Submission and Presentation

### Isaiah
- [ ] Finalize code and submit (April 15)
- [ ] Create deployment instructions
- [ ] Lead final presentation preparation

### Mihiretu
- [ ] Create final presentation slides
- [ ] Prepare demonstration script
- [ ] Highlight technical achievements

### Skeez
- [ ] Ensure all documentation is complete
- [ ] Practice demonstration procedures
- [ ] Prepare for Q&A portions

## Milestones
- [x] Project title and initial presentation (Feb 27, 2025)
- [ ] Interim presentation (March 25, 2025)
- [ ] Final code submission (April 15, 2025)
- [ ] Final demonstration (April 22, 2025)
