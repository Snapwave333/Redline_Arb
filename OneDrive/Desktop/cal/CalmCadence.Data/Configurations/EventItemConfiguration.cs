using CalmCadence.Core.Enums;
using CalmCadence.Core.Models;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace CalmCadence.Data.Configurations;

public class EventItemConfiguration : IEntityTypeConfiguration<EventItem>
{
    public void Configure(EntityTypeBuilder<EventItem> builder)
    {
        builder.ToTable("Events");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Title).IsRequired().HasMaxLength(500);
        builder.Property(e => e.Description).HasMaxLength(4000);
        builder.Property(e => e.Location).HasMaxLength(1000);
        builder.Property(e => e.Source).HasConversion<int>();
        builder.Property(e => e.RecurrenceRule).HasMaxLength(2000);
        builder.Property(e => e.CreatedAt).IsRequired();
        builder.Property(e => e.UpdatedAt).IsRequired();

        builder.HasIndex(e => new { e.Start, e.End });
    }
}
