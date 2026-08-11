import {
    Navigate,
    Route,
    Routes,
} from "react-router-dom";

import Login from "../pages/auth/Login";
import Authenticated from "../pages/auth/Authenticated";
import ProtectedRoute from "./ProtectedRoute";


function AppRoutes() {

    return (
        <Routes>

            <Route
                path="/"
                element={
                    <Navigate
                        to="/login"
                        replace
                    />
                }
            />


            <Route
                path="/login"
                element={<Login />}
            />


            <Route
                path="/authenticated"
                element={
                    <ProtectedRoute>
                        <Authenticated />
                    </ProtectedRoute>
                }
            />


            <Route
                path="*"
                element={
                    <Navigate
                        to="/login"
                        replace
                    />
                }
            />

        </Routes>
    );
}


export default AppRoutes;