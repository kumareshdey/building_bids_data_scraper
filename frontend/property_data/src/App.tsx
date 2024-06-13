import React from 'react';
import DataTable from './AuctionTable';
import './index.css'; // Import the CSS file

const App: React.FC = () => {
    return (
        <div className="app-container">
            <DataTable />
        </div>
    );
};

export default App;
