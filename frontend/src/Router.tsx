import { Redirect, Route, Switch } from "wouter";
import App, { FloatingCopilot } from "@/App";
import { CopilotPage } from "@/pages/copilot";
import { DashboardPage } from "@/pages/dashboard";
import { NotificationsPage } from "@/pages/notifications";
import { AuditPage } from "@/pages/audit";
import { OperationsPage } from "@/pages/operations";
import { ProtocolsPage } from "@/pages/protocols";
import { ScenariosPage } from "@/pages/scenarios";
import { SettingsPage } from "@/pages/settings";
import { TrialsPage } from "@/pages/trials";
import { WorklistPage } from "@/pages/worklist";

export default function RouterApp() {
  return (
    <>
      <Switch>
        <Route path="/" component={DashboardPage} />
        <Route path="/patients" component={App} />
        <Route path="/trials" component={TrialsPage} />
        <Route path="/tasks" component={WorklistPage} />
        <Route path="/analytics" component={OperationsPage} />
        <Route path="/copilot" component={CopilotPage} />
        <Route path="/notifications" component={NotificationsPage} />
        <Route path="/settings" component={SettingsPage} />
        <Route path="/screening"><Redirect to="/patients" /></Route>
        <Route path="/protocols" component={ProtocolsPage} />
        <Route path="/worklist"><Redirect to="/tasks" /></Route>
        <Route path="/operations"><Redirect to="/analytics" /></Route>
        <Route path="/scenarios" component={ScenariosPage} />
        <Route path="/audit" component={AuditPage} />
        <Route><Redirect to="/" /></Route>
      </Switch>
      <FloatingCopilot />
    </>
  );
}
