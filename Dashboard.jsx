import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Biometrics from './Biometrics';
import './Dashboard.css';

export default function Dashboard() {
  const [userData, setUserData] = useState(null);
  const [authAttempts, setAuthAttempts] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('token');
        const username = localStorage.getItem('username');
        
        const [userRes, attemptsRes] = await Promise.all([
          axios.get(`http://localhost:5000/user/${username}`, {
            headers: { Authorization: `Bearer ${token}` }
          }),
          axios.get('http://localhost:5000/auth-attempts', {
            headers: { Authorization: `Bearer ${token}` }
          })
        ]);

        setUserData(userRes.data);
        setAuthAttempts(attemptsRes.data);
      } catch (err) {
        console.error('Dashboard error:', err);
        localStorage.removeItem('token');
        navigate('/login');
      }
    };

    fetchData();
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    navigate('/login');
  };

  if (!userData) {
    return <div className="loading">Loading dashboard...</div>;
  }

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Fraud Detection Dashboard</h1>
        <button onClick={handleLogout} className="logout-btn">
          Logout
        </button>
      </header>

      <div className="dashboard-content">
        <nav className="dashboard-nav">
          <button 
            className={activeTab === 'overview' ? 'active' : ''}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button 
            className={activeTab === 'biometrics' ? 'active' : ''}
            onClick={() => setActiveTab('biometrics')}
          >
            Biometrics
          </button>
          <button 
            className={activeTab === 'activity' ? 'active' : ''}
            onClick={() => setActiveTab('activity')}
          >
            Activity Log
          </button>
        </nav>

        <main className="dashboard-main">
          {activeTab === 'overview' && (
            <div className="overview">
              <div className="stats-card">
                <h3>Risk Score</h3>
                <div className="risk-score">
                  {userData.riskScore || 0}/100
                </div>
                <div 
                  className="risk-bar"
                  style={{ width: `${userData.riskScore || 0}%` }}
                ></div>
              </div>

              <div className="stats-card">
                <h3>Recent Attempts</h3>
                <ul className="attempts-list">
                  {authAttempts.slice(0, 5).map((attempt, index) => (
                    <li key={index} className={attempt.isFraud ? 'fraud' : ''}>
                      {new Date(attempt.timestamp).toLocaleString()} - 
                      {attempt.isFraud ? 'Blocked' : 'Allowed'}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {activeTab === 'biometrics' && <Biometrics data={userData.biometrics} />}

          {activeTab === 'activity' && (
            <div className="activity-log">
              <h2>Authentication History</h2>
              <table>
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>IP Address</th>
                    <th>Location</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {authAttempts.map((attempt, index) => (
                    <tr key={index} className={attempt.isFraud ? 'fraud' : ''}>
                      <td>{new Date(attempt.timestamp).toLocaleString()}</td>
                      <td>{attempt.ipAddress}</td>
                      <td>{attempt.location || 'Unknown'}</td>
                      <td>{attempt.isFraud ? 'Blocked' : 'Allowed'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}