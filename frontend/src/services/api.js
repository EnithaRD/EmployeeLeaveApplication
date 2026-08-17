import axios from "axios";


const api = axios.create({
    baseURL: "http://localhost:8000/api/v1",
    headers: {
        "Content-Type": "application/json",
    },
});


api.interceptors.request.use((config) => {

    const token = localStorage.getItem("access_token");

    if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
});


export async function loginUser(email, password) {

    const formData = new URLSearchParams();

    formData.append("username", email);
    formData.append("password", password);

    const response = await api.post(
        "/auth/login",
        formData,
        {
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
        }
    );

    return response.data;
}


export async function requestOtp(email) {

    const response = await api.post(
        "/auth/otp/request",
        { email }
    );

    return response.data;
}


export async function verifyOtp(email, code) {

    const response = await api.post(
        "/auth/otp/verify",
        { email, code }
    );

    return response.data;
}


export async function signupUser({ email, password, role }) {

    const response = await api.post(
        "/auth/signup",
        { email, password, role }
    );

    return response.data;
}


export async function getCurrentUser(token) {

    const response = await api.get(
        "/auth/me",
        {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        }
    );

    return response.data;
}


export default api;
