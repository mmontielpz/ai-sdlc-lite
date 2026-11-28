// What the repository can show for each scenario. The label states the kind of evidence.
export const scenarios = [
  { id: 'bug-fixing', name: 'Bug fixing', kind: 'Executable example', summary: 'A planted defect fails two of five tests; the repaired file passes all five.' },
  { id: 'feature-implementation', name: 'Feature implementation', kind: 'Documented workflow', summary: 'Agree scope and checks, implement inside them, verify, then accept.' },
  { id: 'brownfield-engineering', name: 'Brownfield engineering', kind: 'Documented workflow · not qualified', summary: 'Inspect first, record the dirty baseline, keep existing work untouched.' },
];
