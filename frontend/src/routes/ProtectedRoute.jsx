import { Navigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";


function ProtectedRoute({ children, allowedRoles }) {

    const {
        user,
        loading,
    } = useAuth();


    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <p className="text-lg">
                    Loading...
                </p>
            </div>
        );
    }


    if (!user) {
        return (
            <Navigate
                to="/login"
                replace
            />
        );
    }


    if (
        Array.isArray(allowedRoles) &&
        allowedRoles.length > 0 &&
        !allowedRoles.includes(user.role)
    ) {
        return (
            <Navigate
                to="/"
                replace
            />
        );
    }


    return children;
}


export default ProtectedRoute;