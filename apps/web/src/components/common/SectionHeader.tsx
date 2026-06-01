interface SectionHeaderProps {
  title: string;
  description?: string;
  meta?: string;
}

export function SectionHeader({ title, description, meta }: SectionHeaderProps) {
  return (
    <div className="section-header">
      <div>
        <h2>{title}</h2>
        {description ? <p>{description}</p> : null}
      </div>
      {meta ? <span>{meta}</span> : null}
    </div>
  );
}
