"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Container, Tabs, Tab, Button } from "react-bootstrap";
import { getCurrentUser, clearCurrentUser } from "../../src/lib/userSession";

export default function TraderPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("trade");
  const [username, setUsername] = useState("");

  useEffect(() => {
    const user = getCurrentUser();
    if (!user || !user.username) {
      router.replace("/login");
    } else {
      setUsername(user.username);
    }
  }, [router]);

  const handleLogout = () => {
    clearCurrentUser();
    router.replace("/login");
  };

  return (
    <Container fluid className="mt-3">

      {/* Top header */}
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h4>Wealth Ocean – MultiBroker Dashboard</h4>
        <div>
          <strong>{username}</strong>{" "}
          <Button size="sm" variant="outline-danger" onClick={handleLogout}>
            Logout
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onSelect={(k) => setActiveTab(k)}
        className="mb-3"
        justify
      >

        <Tab eventKey="trade" title="Trade">
          <h5>Trade Panel</h5>
          <p>This is your TradeForm area (will connect later)</p>
        </Tab>

        <Tab eventKey="orders" title="Orders">
          <h5>Orders</h5>
          <p>Orders will come here</p>
        </Tab>

        <Tab eventKey="positions" title="Positions">
          <h5>Positions</h5>
          <p>Open positions here</p>
        </Tab>

        <Tab eventKey="holdings" title="Holdings">
          <h5>Holdings</h5>
          <p>Your holdings here</p>
        </Tab>

        <Tab eventKey="summary" title="Summary">
          <h5>Summary</h5>
          <p>Account summary here</p>
        </Tab>

        <Tab eventKey="clients" title="Clients">
          <h5>Clients</h5>
          <p>Client management here</p>
        </Tab>

        <Tab eventKey="copy" title="Copy Trading">
          <h5>Copy Trading</h5>
          <p>Copy trading setup here</p>
        </Tab>

      </Tabs>

    </Container>
  );
}
