import type { OnboardingStep } from "@/types";

export const STEP_COPY: Record<OnboardingStep, { title: string; subtitle: string }> = {
  youtube: {
    title: "YouTube history",
    subtitle: "Follow the steps below to export and upload your data.",
  },
};
