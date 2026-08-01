import { Redirect, Route, Switch } from "wouter";
import App from "@/App";
import { AuditPage } from "@/pages/audit";
import { OperationsPage } from "@/pages/operations";
import { ProtocolsPage } from "@/pages/protocols";
import { ScenariosPage } from "@/pages/scenarios";
import { WorklistPage } from "@/pages/worklist";

export default function RouterApp() {
  return (
    <Switch>
      <Route path="/" component={App} />
      <Route path="/screening" component={App} />
      <Route path="/protocols" component={ProtocolsPage} />
      <Route path="/worklist" component={WorklistPage} />
      <Route path="/operations" component={OperationsPage} />
      <Route path="/scenarios" component={ScenariosPage} />
      <Route path="/audit" component={AuditPage} />
      <Route><Redirect to="/" /></Route>
    </Switch>
  );
}
