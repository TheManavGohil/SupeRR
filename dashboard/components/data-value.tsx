import { copy, type CopyKey } from "../content/copy";
import { publicText, type ValueFormat } from "../lib/public-numbers";
export function DataValue({
  source,
  format = "text",
}: {
  source: string;
  format?: ValueFormat;
}) {
  return (
    <span data-json-source={source} data-json-format={format}>
      {publicText(source, format)}
    </span>
  );
}
export function CopyText({ name }: { name: CopyKey }) {
  return <span data-copy-key={name}>{copy[name]}</span>;
}
export function KnownText({ value }: { value: string }) {
  const entry = Object.entries(copy).find(([, text]) => text === value);
  return entry ? <CopyText name={entry[0] as CopyKey} /> : <span>{value}</span>;
}
