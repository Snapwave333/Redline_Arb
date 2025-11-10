using System;
using CalmCadence.Core.Models;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Microsoft.EntityFrameworkCore.Storage.ValueConversion;

namespace CalmCadence.Data.Configurations;

public class HabitLogConfiguration : IEntityTypeConfiguration<HabitLog>
{
    public void Configure(EntityTypeBuilder<HabitLog> builder)
    {
        builder.ToTable("HabitLogs");
        builder.HasKey(l => l.Id);

        // Value converter for DateOnly to DateTime (stored as UTC midnight)
        var dateOnlyConverter = new ValueConverter<DateOnly, DateTime>(
            d => d.ToDateTime(TimeOnly.MinValue, DateTimeKind.Utc),
            dt => DateOnly.FromDateTime(DateTime.SpecifyKind(dt, DateTimeKind.Utc))
        );

        builder.Property(l => l.Date)
               .HasConversion(dateOnlyConverter)
               .HasColumnType("TEXT") // SQLite stores DateTime as TEXT by default
               .IsRequired();

        builder.Property(l => l.Value);
        builder.Property(l => l.Note).HasMaxLength(2000);
        builder.Property(l => l.CreatedAt).IsRequired();

        builder.HasIndex(l => new { l.HabitId, l.Date }).IsUnique();
    }
}
