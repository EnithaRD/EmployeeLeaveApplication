import { useNavigate } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";


function Authenticated() {

    const navigate = useNavigate();

    const {
        user,
        logout,
    } = useAuth();


    const handleLogout = () => {

        logout();

        navigate(
            "/login",
            { replace: true }
        );
    };


    return (
        <div className="min-h-screen bg-gray-100 flex items-center justify-center">

            <div className="bg-white rounded-xl shadow-lg p-8 text-center">

                <h1 className="text-3xl font-bold text-gray-800">
                    Authentication Successful
                </h1>

                <p className="mt-4 text-gray-600">
                    Welcome, {user?.email}
                </p>

                <p className="mt-2 text-gray-600">
                    Role: {user?.role}
                </p>

                <button
                    onClick={handleLogout}
                    className="mt-6 bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700"
                >
                    Logout
                </button>

            </div>

        </div>
    );
}


export default Authenticated;