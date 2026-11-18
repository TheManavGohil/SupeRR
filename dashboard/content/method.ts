import { copy } from "./copy";
export const methodSections = [
  {
    id: "data",
    title: copy.methodDataTitle,
    intro: copy.methodDataIntro,
    points: [copy.methodDataAudit, copy.methodDataWindow],
  },
  {
    id: "pressure",
    title: copy.methodPressureTitle,
    intro: copy.methodPressureIntro,
    points: [
      copy.methodLate,
      copy.methodCollapse,
      copy.methodChase,
      copy.pressureShare,
      copy.verifiedPressureShare,
    ],
  },
  {
    id: "outcomes",
    title: copy.methodOutcomesTitle,
    intro: copy.methodOutcomesIntro,
    points: [copy.methodBatting, copy.methodBowling],
  },
  {
    id: "peers",
    title: copy.methodPeersTitle,
    intro: copy.methodPeersIntro,
    points: [
      copy.methodPeersMinimum,
      copy.methodRecency,
      copy.scoreScopeAdjustment,
    ],
  },
  {
    id: "rating",
    title: copy.methodRatingTitle,
    intro: copy.methodRatingIntro,
    points: [copy.weightPrimary, copy.methodShrinkage, copy.methodEligibility],
  },
  {
    id: "uncertainty",
    title: copy.methodBootstrapTitle,
    intro: copy.methodBootstrapIntro,
    points: [copy.methodBootstrapGate, copy.methodBootstrapLimit],
  },
  {
    id: "usual",
    title: copy.methodUsualTitle,
    intro: copy.methodUsualIntro,
    points: [copy.weightLevel, copy.weightLevelEqual, copy.companions],
  },
  {
    id: "validation",
    title: copy.methodValidationTitle,
    intro: copy.methodValidationIntro,
    points: [
      copy.retrospective,
      copy.weightEqual,
      copy.weightRuns,
      copy.eligibility,
    ],
  },
];
