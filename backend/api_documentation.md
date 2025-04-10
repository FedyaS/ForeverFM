
# API Documentation

## Base URL
```
https://flask-backend-z6zx.onrender.com
```

### **1. POST `/chat-prompt`**

#### **Request**
- **Method**: `POST`
- **URL**: `/chat-prompt`
- **Headers**:
    - `Content-Type: application/json`
- **Body**:
    ```json
    {
        "user_prompt": "Your prompt text here"
    }
    ```

#### **Request Body Schema**
- `user_prompt` (string): The prompt that the user wants to add to the conversation.

#### **Response**
- **Status Code**: `200 OK`
- **Body**:
    ```json
    {
        "message": "Prompt added to queue"
    }
    ```

#### **Response Schema**
- `message` (string): A success message confirming the prompt was added to the queue.

---

### **2. GET `/audio`**

#### **Request**
- **Method**: `GET`
- **URL**: `/audio`
- **Headers**: None required

#### **Response**
- **Status Code**: `200 OK` (if audio file is available)
- **Body**: Audio file (`.wav`).
    - The audio file will be returned as the content of the response.

- **Status Code**: `404 Not Found` (if no audio files are available)
- **Body**:
    ```json
    {
        "message": "No audio files available"
    }
    ```

#### **Response Schema**
- `message` (string): A message indicating whether audio is available or not.

---

### **3. Error Handling**

#### **Common Error Responses**
1. **400 Bad Request**: This error is returned when the request body is malformed or missing required fields.
    - **Response**:
    ```json
    {
        "error": "Bad Request",
        "message": "User input is required"
    }
    ```

2. **404 Not Found**: This error occurs when the requested resource cannot be found, such as when there is no audio file available.
    - **Response**:
    ```json
    {
        "message": "No audio files available"
    }
    ```

---

### **Schema Summary**
| Endpoint         | Method | Request Body | Response Body  |
|------------------|--------|--------------|----------------|
| `/chat-prompt`   | POST   | `{"user_prompt": "string"}` | `{"message": "Prompt added to queue"}` |
| `/audio`         | GET    | None         | Audio file or `{"message": "No audio files available"}` |

---
