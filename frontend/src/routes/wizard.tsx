import { createFileRoute, Outlet } from "@tanstack/react-router";
import { WizardShell } from "@/components/venture/WizardLayout";

export const Route = createFileRoute("/wizard")({
  head: () => ({ meta: [{ title: "Venture Wizard · VentureMind AI" }, { name: "description", content: "Seven-step guided venture analysis." }] }),
  component: () => (
    <WizardShell>
      <Outlet />
    </WizardShell>
  ),
});