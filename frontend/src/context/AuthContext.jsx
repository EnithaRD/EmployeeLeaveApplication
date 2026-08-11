import {
    createContext,
    useContext,
    useEffect,
    useState,
} from "react";

import {
    getCurrentUser,
    loginUser,
} from "../services/api";


const AuthContext = createContext(null);


export function AuthProvider({ children }) {

    const [user, setUser] = useState(null);
    const [token, setToken] = useState(
        localStorage.getItem("access_token")
    );
    const [loading, setLoading] = useState(true);


    useEffect(() => {

        const loadUser = async () => {

            if (!token) {
                setLoading(false);
                return;
            }

            try {

                const currentUser =
                    await getCurrentUser(token);

                setUser(currentUser);

            } catch (error) {

                localStorage.removeItem(
                    "access_token"
                );

                setToken(null);
                setUser(null);

            } finally {

                setLoading(false);

            }
        };


        loadUser();

    }, [token]);


    const login = async (email, password) => {

        const data = await loginUser(
            email,
            password
        );

        localStorage.setItem(
            "access_token",
            data.access_token
        );

        setToken(data.access_token);

        const currentUser =
            await getCurrentUser(
                data.access_token
            );

        setUser(currentUser);

        return currentUser;
    };


    const logout = () => {

        localStorage.removeItem(
            "access_token"
        );

        setToken(null);
        setUser(null);
    };


    return (
        <AuthContext.Provider
            value={{
                user,
                token,
                loading,
                login,
                logout,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}


export function useAuth() {
    return useContext(AuthContext);
}