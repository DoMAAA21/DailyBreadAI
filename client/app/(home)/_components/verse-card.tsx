import { Quote } from "lucide-react";

type VerseCardProps = {
  text: string;
  reference: string;
};

export function VerseCard({ text, reference }: VerseCardProps) {
  return (
    <div className="rounded-xl bg-royal-indigo p-5 text-aged-parchment shadow-md">
      <Quote className="mb-3 size-5 text-sacred-gold" />
      <p className="text-[15px] leading-relaxed">{text}</p>
      <p className="mt-3 text-sm font-medium text-sacred-gold">— {reference}</p>
    </div>
  );
}
