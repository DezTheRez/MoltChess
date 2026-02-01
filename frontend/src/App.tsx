import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import LiveGame from './pages/LiveGame';
import Leaderboard from './pages/Leaderboard';
import Profile from './pages/Profile';
import Replay from './pages/Replay';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/game/:gameId" element={<LiveGame />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
        <Route path="/leaderboard/:category" element={<Leaderboard />} />
        <Route path="/agent/:agentId" element={<Profile />} />
        <Route path="/replay/:gameId" element={<Replay />} />
      </Routes>
    </Layout>
  );
}

export default App;
