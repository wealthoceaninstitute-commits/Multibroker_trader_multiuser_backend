"use client";

import { useState } from "react";
import TradeForm from "@/components/TradeForm";
import Orders from "@/components/Orders";
import Positions from "@/components/Positions";
import Holdings from "@/components/Holdings";
import Summary from "@/components/Summary";
import Clients from "@/components/Clients";
import CopyTrading from "@/components/CopyTrading";

export default function TradePage() {
  const [tab, setTab] = useState("trade");

  const renderTab = () => {
    switch (tab) {
      case "orders": return <Orders />;
      case "positions": return <Positions />;
      case "holdings": return <Holdings />;
      case "summary": return <Summary />;
      case "clients": return <Clients />;
      case "copy": return <CopyTrading />;
      default: return <TradeForm />;
    }
  };

  return (
    <div style={{ padding: 20 }}>

      <nav style={{
        display: "flex",
        gap: 20,
        borderBottom: "1px solid #e5e7eb",
        paddingBottom: 10,
        marginBottom: 20,
        flexWrap: "wrap"
      }}>

        <Tab label="Trade" value="trade" tab={tab} setTab={setTab}/>
        <Tab label="Orders" value="orders" tab={tab} setTab={setTab}/>
        <Tab label="Positions" value="positions" tab={tab} setTab={setTab}/>
        <Tab label="Holdings" value="holdings" tab={tab} setTab={setTab}/>
        <Tab label="Summary" value="summary" tab={tab} setTab={setTab}/>
        <Tab label="Clients" value="clients" tab={tab} setTab={setTab}/>
        <Tab label="Copy Trading" value="copy" tab={tab} setTab={setTab}/>

      </nav>

      {renderTab()}
    </div>
  );
}

function Tab({ label, value, tab, setTab }) {
  const isActive = tab === value;

  return (
    <button
      onClick={() => setTab(value)}
      style={{
        border: "none",
        background: "transparent",
        color: isActive ? "#2563eb" : "#374151",
        fontWeight: isActive ? "bold" : "normal",
        borderBottom: isActive ? "2px solid #2563eb" : "none",
        paddingBottom: 5,
        cursor: "pointer"
      }}
    >
      {label}
    </button>
  );
}
