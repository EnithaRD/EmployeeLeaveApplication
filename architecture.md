# Architecture

## Overview
EmployeeLeaveApplication is a web application for managing employee leave requests and approvals.

## Backend
The backend is built with Python and handles API requests, business logic, authentication, and database operations.

## Database
Database-related code is organized under `backend/app/db/`, while configuration is maintained under `backend/app/core/`.

## Configuration
Environment-specific values are stored in `.env` and should not be committed to Git.

## Request Flow
```text
Client → API → Business Logic → Database